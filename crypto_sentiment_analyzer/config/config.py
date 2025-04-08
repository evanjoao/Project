import os
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
import yaml
import json
import redis
from functools import lru_cache
import logging
from pathlib import Path
import hashlib
from datetime import datetime, timedelta
import aiohttp
import asyncio
from ratelimit import limits, sleep_and_retry
from enum import Enum
import pydantic
from pydantic import BaseModel, field_validator
import time

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Environment(str, Enum):
    """Entornos de ejecución disponibles"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class ProxyConfig(BaseModel):
    """Configuración de proxies con validación"""
    proxy_list: List[str]
    proxy_auth: Optional[Dict[str, str]] = None
    proxy_timeout: int = 30
    max_retries: int = 3
    rotation_interval: int = 300
    health_check_interval: int = 60
    min_working_proxies: int = 3
    retry_delay: int = 5

    @field_validator('proxy_list')
    @classmethod
    def validate_proxy_list(cls, v):
        if not v:
            raise ValueError("La lista de proxies no puede estar vacía")
        return v

    @field_validator('proxy_timeout', 'max_retries', 'rotation_interval', 'health_check_interval')
    @classmethod
    def validate_positive_integers(cls, v):
        if v <= 0:
            raise ValueError("El valor debe ser positivo")
        return v

class ScraperConfig(BaseModel):
    """Configuración del scraper con validación"""
    user_agent: str
    request_timeout: int = 30
    max_concurrent_requests: int = 10
    rate_limit: int = 60
    batch_size: int = 100
    retry_delay: int = 5
    max_retries: int = 3

    @field_validator('user_agent')
    @classmethod
    def validate_user_agent(cls, v):
        if not v:
            raise ValueError("El user agent no puede estar vacío")
        return v

    @field_validator('request_timeout', 'max_concurrent_requests', 'rate_limit', 'batch_size', 'retry_delay', 'max_retries')
    @classmethod
    def validate_positive_integers(cls, v):
        if v <= 0:
            raise ValueError("El valor debe ser positivo")
        return v

class SentimentConfig(BaseModel):
    """Configuración del análisis de sentimiento con validación"""
    model_path: str
    batch_size: int = 32
    cache_ttl: int = 3600
    min_confidence: float = 0.6
    update_interval: int = 300
    max_text_length: int = 512
    language: str = "en"

    @field_validator('model_path')
    @classmethod
    def validate_model_path(cls, v):
        if not Path(v).exists():
            raise ValueError(f"El modelo no existe en la ruta: {v}")
        return v

    @field_validator('min_confidence')
    @classmethod
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("La confianza debe estar entre 0 y 1")
        return v

class CacheConfig(BaseModel):
    """Configuración del sistema de caché con validación"""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    default_ttl: int = 300
    max_memory: str = "2gb"
    max_memory_policy: str = "allkeys-lru"

    @field_validator('max_memory_policy')
    @classmethod
    def validate_memory_policy(cls, v):
        valid_policies = ['allkeys-lru', 'volatile-lru', 'allkeys-random', 'volatile-random', 'volatile-ttl']
        if v not in valid_policies:
            raise ValueError(f"Política de memoria inválida. Debe ser una de: {valid_policies}")
        return v

class Config(BaseModel):
    """Configuración global con validación"""
    environment: Environment = Environment.DEVELOPMENT
    proxy: ProxyConfig
    scraper: ScraperConfig
    sentiment: SentimentConfig
    cache: CacheConfig
    data_dir: str = "data"
    temp_dir: str = "temp"
    log_level: str = "INFO"
    debug: bool = False

    class Config:
        arbitrary_types_allowed = True

class ConfigManager:
    """Gestor de configuración con caché y validación mejorada"""
    
    def __init__(self, config_path: str = "config.yaml", environment: Environment = Environment.DEVELOPMENT):
        self.config_path = config_path
        self.environment = environment
        self._config: Optional[Config] = None
        self._redis_client: Optional[redis.Redis] = None
        self._config_hash: Optional[str] = None
        self._proxy_pool: List[str] = []
        self._proxy_last_rotation: Optional[datetime] = None
        self._proxy_lock = asyncio.Lock()
        self._load_dotenv()
    
    def _load_dotenv(self):
        """Carga variables de entorno según el ambiente"""
        env_file = f".env.{self.environment.value}"
        if Path(env_file).exists():
            load_dotenv(env_file)
        else:
            load_dotenv()

    @property
    def config(self) -> Config:
        """Obtiene la configuración, usando caché si está disponible"""
        if self._config is None:
            self._load_config()
        return self._config

    def _load_config(self):
        """Carga la configuración desde el archivo con manejo de errores mejorado"""
        try:
            if not Path(self.config_path).exists():
                raise FileNotFoundError(f"Archivo de configuración no encontrado: {self.config_path}")

            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Validar estructura básica
            required_sections = ['proxy', 'scraper', 'sentiment', 'cache']
            for section in required_sections:
                if section not in config_data:
                    raise ValueError(f"Sección requerida no encontrada en la configuración: {section}")

            # Calcular hash de la configuración
            config_str = json.dumps(config_data, sort_keys=True)
            self._config_hash = hashlib.md5(config_str.encode()).hexdigest()
            
            # Verificar caché de Redis
            cached_config = self._get_cached_config()
            if cached_config is not None:
                self._config = cached_config
                return
            
            # Crear objetos de configuración con validación
            self._config = Config(
                environment=self.environment,
                proxy=ProxyConfig(**config_data['proxy']),
                scraper=ScraperConfig(**config_data['scraper']),
                sentiment=SentimentConfig(**config_data['sentiment']),
                cache=CacheConfig(**config_data['cache']),
                **config_data.get('app', {})
            )
            
            # Guardar en caché
            self._cache_config()
            
        except Exception as e:
            logger.error(f"Error al cargar configuración: {str(e)}", exc_info=True)
            raise
    
    def _get_redis_client(self) -> redis.Redis:
        """Obtiene el cliente de Redis con manejo de errores mejorado"""
        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis(
                    host=self.config.cache.redis_host,
                    port=self.config.cache.redis_port,
                    db=self.config.cache.redis_db,
                    decode_responses=True,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                
                # Verificar conexión
                self._redis_client.ping()
                
                # Configurar límites de memoria
                self._redis_client.config_set(
                    'maxmemory', self.config.cache.max_memory
                )
                self._redis_client.config_set(
                    'maxmemory-policy', self.config.cache.max_memory_policy
                )
                
            except redis.ConnectionError as e:
                logger.error(f"Error de conexión con Redis: {str(e)}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"Error al configurar Redis: {str(e)}", exc_info=True)
                raise
        
        return self._redis_client
    
    def _get_cached_config(self) -> Optional[Config]:
        """Obtiene la configuración desde caché con manejo de errores mejorado"""
        try:
            redis_client = self._get_redis_client()
            
            # Obtener configuración cacheada
            cached_data = redis_client.get('sentiment_config')
            if cached_data is None:
                return None
            
            try:
                cached_config = json.loads(cached_data)
            except json.JSONDecodeError as e:
                logger.error(f"Error al decodificar configuración cacheada: {str(e)}")
                return None
            
            # Verificar hash
            if cached_config.get('hash') != self._config_hash:
                logger.info("Hash de configuración no coincide, ignorando caché")
                return None
            
            try:
                # Crear objeto Config con validación
                return Config(
                    environment=self.environment,
                    proxy=ProxyConfig(**cached_config['proxy']),
                    scraper=ScraperConfig(**cached_config['scraper']),
                    sentiment=SentimentConfig(**cached_config['sentiment']),
                    cache=CacheConfig(**cached_config['cache']),
                    **cached_config['app']
                )
            except pydantic.ValidationError as e:
                logger.error(f"Error de validación en configuración cacheada: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Error al obtener configuración cacheada: {str(e)}", exc_info=True)
            return None
    
    def _cache_config(self):
        """Guarda la configuración en caché con manejo de errores mejorado"""
        try:
            redis_client = self._get_redis_client()
            
            # Convertir a diccionario
            config_dict = {
                'hash': self._config_hash,
                'proxy': self.config.proxy.dict(),
                'scraper': self.config.scraper.dict(),
                'sentiment': self.config.sentiment.dict(),
                'cache': self.config.cache.dict(),
                'app': {
                    'data_dir': self.config.data_dir,
                    'temp_dir': self.config.temp_dir,
                    'log_level': self.config.log_level,
                    'debug': self.config.debug
                }
            }
            
            # Guardar en Redis con manejo de errores
            try:
                redis_client.setex(
                    'sentiment_config',
                    self.config.cache.default_ttl,
                    json.dumps(config_dict)
                )
                logger.info("Configuración guardada en caché exitosamente")
            except redis.RedisError as e:
                logger.error(f"Error al guardar en Redis: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error al cachear configuración: {str(e)}", exc_info=True)
    
    @lru_cache(maxsize=100)
    def get_setting(self, key: str) -> Any:
        """
        Obtiene un valor de configuración específico con validación
        
        Args:
            key: Clave del valor a obtener (ej: "proxy.proxy_list")
            
        Returns:
            Any: Valor de la configuración
            
        Raises:
            ValueError: Si la clave no existe o es inválida
        """
        try:
            value = self.config
            for k in key.split('.'):
                if not hasattr(value, k):
                    raise ValueError(f"Clave de configuración inválida: {key}")
                value = getattr(value, k)
            return value
            
        except Exception as e:
            logger.error(f"Error al obtener configuración {key}: {str(e)}", exc_info=True)
            raise ValueError(f"Error al obtener configuración {key}: {str(e)}")
    
    async def get_proxy(self) -> Optional[str]:
        """
        Obtiene un proxy del pool con rotación y verificación de salud mejorada
        
        Returns:
            Optional[str]: URL del proxy o None si no hay disponibles
            
        Raises:
            Exception: Si hay un error al obtener el proxy
        """
        try:
            async with self._proxy_lock:
                # Verificar si necesitamos rotar proxies
                if (self._proxy_last_rotation is None or
                        (datetime.now() - self._proxy_last_rotation
                         ).total_seconds() > self.config.proxy.rotation_interval):
                    await self._rotate_proxies()
                
                # Verificar si tenemos suficientes proxies
                if len(self._proxy_pool) < self.config.proxy.min_working_proxies:
                    await self._rotate_proxies()
                
                if not self._proxy_pool:
                    logger.warning("No hay proxies disponibles en el pool")
                    return None
                
                # Obtener siguiente proxy
                proxy = self._proxy_pool.pop(0)
                self._proxy_pool.append(proxy)
                
                return proxy
                
        except Exception as e:
            logger.error(f"Error al obtener proxy: {str(e)}", exc_info=True)
            raise
    
    async def _rotate_proxies(self):
        """Rota y verifica la salud de los proxies con manejo de errores mejorado"""
        try:
            # Obtener lista de proxies
            proxies = self.config.proxy.proxy_list.copy()
            
            if not proxies:
                logger.error("No hay proxies configurados")
                return
            
            # Verificar salud de proxies
            async with aiohttp.ClientSession() as session:
                tasks = []
                for proxy in proxies:
                    task = asyncio.create_task(self._check_proxy_health(session, proxy))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filtrar proxies saludables
                self._proxy_pool = [
                    proxy for proxy, is_healthy in zip(proxies, results)
                    if isinstance(is_healthy, bool) and is_healthy
                ]
            
            self._proxy_last_rotation = datetime.now()
            
            if not self._proxy_pool:
                logger.error("No se encontraron proxies saludables")
            else:
                logger.info(f"Pool de proxies actualizado: {len(self._proxy_pool)} proxies saludables")
            
            # Iniciar verificación periódica
            asyncio.create_task(self._periodic_health_check())
            
        except Exception as e:
            logger.error(f"Error al rotar proxies: {str(e)}", exc_info=True)
            raise
    
    async def _check_proxy_health(self, session: aiohttp.ClientSession,
                                proxy: str) -> bool:
        """
        Verifica la salud de un proxy con timeout y reintentos
        
        Args:
            session: Sesión HTTP
            proxy: URL del proxy
            
        Returns:
            bool: True si el proxy está saludable
        """
        for attempt in range(self.config.proxy.max_retries):
            try:
                async with session.get(
                    'https://api.ipify.org?format=json',
                    proxy=proxy,
                    timeout=self.config.proxy.proxy_timeout
                ) as response:
                    if response.status == 200:
                        return True
                    
            except asyncio.TimeoutError:
                logger.warning(f"Timeout al verificar proxy {proxy}")
            except Exception as e:
                logger.warning(f"Error al verificar proxy {proxy}: {str(e)}")
            
            if attempt < self.config.proxy.max_retries - 1:
                await asyncio.sleep(self.config.proxy.retry_delay)
        
        return False
    
    async def _periodic_health_check(self):
        """Verifica periódicamente la salud de los proxies con manejo de errores mejorado"""
        while True:
            try:
                await asyncio.sleep(self.config.proxy.health_check_interval)
                
                if len(self._proxy_pool) < self.config.proxy.min_working_proxies:
                    logger.warning("Pool de proxies por debajo del mínimo, iniciando rotación")
                    await self._rotate_proxies()
                    
            except Exception as e:
                logger.error(f"Error en verificación periódica de proxies: {str(e)}", exc_info=True)
                await asyncio.sleep(self.config.proxy.retry_delay)
    
    @sleep_and_retry
    @limits(calls=60, period=60)
    def check_rate_limit(self):
        """
        Verifica el rate limit usando Redis con manejo de errores mejorado
        
        Raises:
            Exception: Si se excede el rate limit
        """
        try:
            current = int(time.time())
            key = f"sentiment_rate:{current // 60}"
            
            pipe = self._get_redis_client().pipeline()
            pipe.incr(key)
            pipe.expire(key, 60)
            result = pipe.execute()
            
            if result[0] > self.config.scraper.rate_limit:
                raise Exception("Rate limit exceeded")
                
        except redis.RedisError as e:
            logger.error(f"Error de Redis al verificar rate limit: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error al verificar rate limit: {str(e)}", exc_info=True)
            raise
    
    def clear_cache(self):
        """Limpia la caché de configuración con manejo de errores mejorado"""
        try:
            # Limpiar caché de Redis
            redis_client = self._get_redis_client()
            redis_client.delete('sentiment_config')
            
            # Limpiar caché local
            self._config = None
            self._config_hash = None
            self.get_setting.cache_clear()
            
            logger.info("Caché de configuración limpiada exitosamente")
            
        except Exception as e:
            logger.error(f"Error al limpiar caché: {str(e)}", exc_info=True)
            raise
    
    def validate_config(self) -> bool:
        """
        Valida la configuración actual con verificaciones mejoradas
        
        Returns:
            bool: True si la configuración es válida
            
        Raises:
            ValueError: Si la configuración no es válida
        """
        try:
            # Validar directorios
            Path(self.config.data_dir).mkdir(parents=True, exist_ok=True)
            Path(self.config.temp_dir).mkdir(parents=True, exist_ok=True)
            
            # Validar conexión a Redis
            redis_client = self._get_redis_client()
            redis_client.ping()
            
            # Validar proxies
            if not self.config.proxy.proxy_list:
                raise ValueError("No hay proxies configurados")
            
            # Validar modelo de sentimiento
            if not Path(self.config.sentiment.model_path).exists():
                raise ValueError(
                    f"Modelo de sentimiento no encontrado: {self.config.sentiment.model_path}"
                )
            
            # Validar configuración de caché
            if not self.config.cache.max_memory.endswith(('mb', 'gb')):
                raise ValueError("max_memory debe terminar en 'mb' o 'gb'")
            
            logger.info("Configuración validada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al validar configuración: {str(e)}", exc_info=True)
            raise ValueError(f"Error de validación: {str(e)}")
    
    def close(self):
        """Cierra las conexiones con manejo de errores mejorado"""
        try:
            if self._redis_client is not None:
                self._redis_client.close()
                self._redis_client = None
                logger.info("Conexiones cerradas exitosamente")
        except Exception as e:
            logger.error(f"Error al cerrar conexiones: {str(e)}", exc_info=True)
            raise

# Instancia global del gestor de configuración
config_manager = ConfigManager()

# Función helper para obtener configuración
def get_config(key: str) -> Any:
    """
    Obtiene un valor de configuración con manejo de errores mejorado
    
    Args:
        key: Clave del valor a obtener
        
    Returns:
        Any: Valor de la configuración
        
    Raises:
        ValueError: Si la clave no existe o es inválida
    """
    try:
        return config_manager.get_setting(key)
    except Exception as e:
        logger.error(f"Error al obtener configuración {key}: {str(e)}", exc_info=True)
        raise ValueError(f"Error al obtener configuración {key}: {str(e)}")

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = 'crypto_sentiment.log'

# Configuración de scraping
MAX_SCROLLS = int(os.getenv('MAX_SCROLLS', '50'))
DELAY_MIN = float(os.getenv('DELAY_MIN', '2'))
DELAY_MAX = float(os.getenv('DELAY_MAX', '5'))

# Configuración de proxies
PROXY_LIST = os.getenv('PROXY_LIST', '').split(',')
PROXY_USERNAME = os.getenv('PROXY_USERNAME', '')
PROXY_PASSWORD = os.getenv('PROXY_PASSWORD', '')

# Configuración de directorios
RESULTS_DIR = 'results'
os.makedirs(RESULTS_DIR, exist_ok=True)

# Configuración de cuentas a analizar
ACCOUNTS = {
    'elonmusk': 'Elon Musk',
    'cz_binance': 'Changpeng Zhao',
    'VitalikButerin': 'Vitalik Buterin',
    'nayibbukele': 'Nayib Bukele',
    'saylor': 'Michael Saylor',
    'brian_armstrong': 'Brian Armstrong',
    'APompliano': 'Anthony Pompliano',
    'TheCryptoLark': 'Lark Davis',
    'woonomic': 'Willy Woo',
    'RaoulGMI': 'Raoul Pal'
}

# Palabras clave para análisis
CRYPTO_KEYWORDS = [
    'bitcoin', 'btc', 'crypto', 'blockchain', 'eth', 'ethereum',
    'defi', 'nft', 'web3', 'mining', 'hodl', 'altcoin', 'token',
    'wallet', 'exchange', 'binance', 'coinbase', 'metaverse'
]

# User agents para rotación
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
]

# Configuración del modelo de sentimiento
SENTIMENT_MODEL = "finiteautomata/bertweet-base-sentiment-analysis" 