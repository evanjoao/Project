import os
import time
import hmac
import hashlib
import json
import logging
import threading
import websocket
from websocket._app import WebSocketApp
import requests
from typing import Dict, List, Optional, Union, Any, Callable, Tuple, cast, TypedDict
from urllib.parse import urlencode
from functools import lru_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from decimal import Decimal
import sys
from dotenv import load_dotenv
from datetime import datetime
import asyncio
import aiohttp
from aiohttp import ClientResponse, ClientSession
from .exchange_interface import (
    ExchangeInterface, OrderType, OrderSide, OrderStatus,
    OrderInfo, TradeInfo, OrderBookEntry
)
from .api_types import (
    BinanceOrderResponse, BinanceOrderBookResponse,
    BinanceTradeResponse, BinanceBalanceResponse,
    BinanceTickerResponse, BinanceWebsocketMessage,
    Timestamp
)

# Use absolute imports for exceptions defined within the same 'api' package
from src.api.exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    InvalidRequestError,
    InsufficientFundsError,
    NetworkError,
    InvalidResponseError
)
# Keep other potentially correct imports
from src.utils.logger import get_logger

logger = get_logger(__name__)

class BinanceKlineResponse(TypedDict):
    open_time: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    close_time: int
    quote_volume: str
    trades: int
    taker_buy_base_volume: str
    taker_buy_quote_volume: str

class KlineInfo(TypedDict):
    symbol: str
    open_time: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    close_time: datetime
    quote_volume: Decimal
    trades_count: int
    taker_buy_base_volume: Decimal
    taker_buy_quote_volume: Decimal

class BinanceAPI(ExchangeInterface):
    """
    Implementación de la API de Binance para interactuar con el exchange.
    
    Esta clase proporciona métodos para:
    - Obtener datos de mercado (precios, velas, etc.)
    - Gestionar cuentas y balances
    - Crear y gestionar órdenes de trading
    - Suscribirse a streams de datos en tiempo real
    
    Ejemplo de uso:
    ```python
    # Inicializar la API
    api = BinanceAPI(api_key="tu_api_key", api_secret="tu_api_secret")
    
    # Obtener precio actual de BTC
    btc_price = api.get_symbol_price("BTCUSDT")
    
    # Crear una orden de compra
    order = api.create_order(
        symbol="BTCUSDT",
        side="BUY",
        order_type="MARKET",
        quantity=0.001
    )
    
    # Suscribirse a actualizaciones de precio
    def price_callback(data):
        print(f"Nuevo precio de BTC: {data['p']}")
    
    api.subscribe_to_ticker("btcusdt", price_callback)
    ```
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, 
                 testnet: bool = False, timeout: int = 10, max_retries: int = 3):
        """
        Inicializa la API de Binance.
        
        Args:
            api_key: Clave API de Binance
            api_secret: Secreto API de Binance
            testnet: Si es True, usa el entorno de prueba de Binance
            timeout: Tiempo de espera para las solicitudes en segundos
            max_retries: Número máximo de reintentos para solicitudes fallidas
        """
        self.api_key = api_key or os.environ.get('BINANCE_API_KEY')
        self.api_secret = api_secret or os.environ.get('BINANCE_API_SECRET')
        self.testnet = testnet
        self.timeout = timeout
        self.max_retries = max_retries
        
        # URLs base
        if testnet:
            self.base_url = 'https://testnet.binance.vision/api'
            self.futures_url = 'https://testnet.binancefuture.com/fapi'
            self.ws_url = 'wss://testnet.binance.vision/ws'
        else:
            self.base_url = 'https://api.binance.com/api'
            self.futures_url = 'https://fapi.binance.com'
            self.ws_url = 'wss://stream.binance.com:9443/ws'
        
        # Configurar sesión de requests con reintentos
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # WebSocket connections
        self.ws_connections = {}
        self.ws_threads = {}
        self.ws_callbacks = {}  # Store callbacks separately
        
        # Verificar credenciales
        if not self.api_key or not self.api_secret:
            logger.warning("API key o secret no proporcionados. Algunas funciones estarán limitadas.")
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Genera una firma HMAC SHA256 para autenticar solicitudes.
        
        Args:
            params: Parámetros de la solicitud
            
        Returns:
            Firma generada
        """
        if not self.api_secret:
            raise ValueError("API secret is required for signed requests")
            
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                signed: bool = False, futures: bool = False) -> Dict[str, Any]:
        """
        Realiza una solicitud a la API de Binance.
        
        Args:
            method: Método HTTP ('GET', 'POST', etc.)
            endpoint: Endpoint de la API
            params: Parámetros de la solicitud
            signed: Si la solicitud requiere firma
            futures: Si la solicitud es para la API de futuros
            
        Returns:
            Respuesta de la API en formato JSON
            
        Raises:
            APIError: Error general de la API
            AuthenticationError: Error de autenticación
            RateLimitError: Error de límite de tasa
            InvalidRequestError: Error en la solicitud
        """
        # Seleccionar la URL base según el tipo de API
        if futures:
            if not self.futures_url:
                raise APIError("URL de futuros no configurada")
            url = f"{self.futures_url}{endpoint}"
        else:
            url = f"{self.base_url}{endpoint}"
            
        # Configurar headers
        headers = {}
        if self.api_key:
            headers['X-MBX-APIKEY'] = self.api_key
            
        if params is None:
            params = {}
            
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
            
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params if method == 'GET' else None,
                data=params if method != 'GET' else None,
                timeout=self.timeout
            )
            
            # Manejar errores HTTP
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_code = error_data.get('code', 0)
                    error_msg = error_data.get('msg', 'Unknown error')
                    
                    if response.status_code == 401:
                        raise AuthenticationError(f"Error de autenticación: {error_msg}")
                    elif response.status_code == 429:
                        raise RateLimitError(f"Límite de tasa excedido: {error_msg}")
                    elif response.status_code == 400:
                        raise InvalidRequestError(f"Solicitud inválida: {error_msg}")
                    else:
                        raise APIError(f"Error de API ({error_code}): {error_msg}")
                except ValueError:
                    raise APIError(f"Error de API: {response.text}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en la solicitud a Binance: {str(e)}")
            raise APIError(f"Error en la solicitud: {str(e)}")
    
    # Métodos de mercado
    
    @lru_cache(maxsize=100)
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre los pares de trading disponibles.
        
        Returns:
            Información del exchange
        """
        return self._request('GET', '/v3/exchangeInfo')
    
    def get_symbol_price(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene el precio actual de un símbolo.
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            
        Returns:
            Información del precio
        """
        return self._request('GET', '/v3/ticker/price', {'symbol': symbol})
    
    async def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[KlineInfo]:
        """Get kline/candlestick data."""
        endpoint = '/v3/klines'
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': limit
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}{endpoint}", params=params) as response:
                response.raise_for_status()
                data = await response.json()
                return [
                    KlineInfo(
                        symbol=symbol,
                        open_time=self._convert_timestamp(int(kline[0])),
                        open_price=Decimal(str(kline[1])),
                        high_price=Decimal(str(kline[2])),
                        low_price=Decimal(str(kline[3])),
                        close_price=Decimal(str(kline[4])),
                        volume=Decimal(str(kline[5])),
                        close_time=self._convert_timestamp(int(kline[6])),
                        quote_volume=Decimal(str(kline[7])),
                        trades_count=int(kline[8]),
                        taker_buy_base_volume=Decimal(str(kline[9])),
                        taker_buy_quote_volume=Decimal(str(kline[10]))
                    )
                    for kline in data
                ]
    
    # Métodos de cuenta
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Obtiene información de la cuenta.
        
        Returns:
            Información de la cuenta
        """
        return self._request('GET', '/api/v3/account', signed=True)
    
    def get_balance(self, asset: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Obtiene el balance de la cuenta.
        
        Args:
            asset: Activo específico (opcional)
            
        Returns:
            Balance de la cuenta
        """
        account = self.get_account_info()
        balances = account.get('balances', [])
        
        if asset:
            for balance in balances:
                if balance['asset'] == asset:
                    return balance
            return {}
        
        return balances
    
    # Métodos de trading
    
    def create_order(self, symbol: str, side: str, order_type: str, 
                    quantity: Optional[float] = None, price: Optional[float] = None,
                    time_in_force: Optional[str] = None, 
                    stop_price: Optional[float] = None,
                    iceberg_qty: Optional[float] = None) -> Dict[str, Any]:
        """
        Crea una orden de trading.
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            side: Lado de la orden ('BUY' o 'SELL')
            order_type: Tipo de orden ('LIMIT', 'MARKET', etc.)
            quantity: Cantidad a comprar/vender
            price: Precio para órdenes limit
            time_in_force: Tiempo en vigor para órdenes limit ('GTC', 'IOC', 'FOK')
            stop_price: Precio de parada para órdenes stop
            iceberg_qty: Cantidad iceberg para órdenes iceberg
            
        Returns:
            Información de la orden creada
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type
        }
        
        if quantity:
            params['quantity'] = str(quantity)
        if price:
            params['price'] = str(price)
        if time_in_force:
            params['timeInForce'] = time_in_force
        elif order_type == 'LIMIT':  # Add default timeInForce for LIMIT orders
            params['timeInForce'] = 'GTC'
        if stop_price:
            params['stopPrice'] = str(stop_price)
        if iceberg_qty:
            params['icebergQty'] = str(iceberg_qty)
            
        return self._request('POST', '/v3/order', params, signed=True)
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an order."""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._request('DELETE', '/v3/order', params, signed=True)
    
    def get_order(self, symbol: str, order_id: Optional[int] = None, 
                 orig_client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene información de una orden específica.
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            order_id: ID de la orden
            orig_client_order_id: ID de cliente original de la orden
            
        Returns:
            Información de la orden
        """
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = str(order_id)
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
            
        return self._request('GET', '/v3/order', params, signed=True)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todas las órdenes abiertas.
        
        Args:
            symbol: Par de trading (opcional)
            
        Returns:
            Lista de órdenes abiertas
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
            
        response = self._request('GET', '/v3/openOrders', params, signed=True)
        # The response is a list, not a dict
        return response if isinstance(response, list) else []
    
    def get_all_orders(self, symbol: str, order_id: Optional[int] = None, 
                      start_time: Optional[int] = None, end_time: Optional[int] = None,
                      limit: int = 500) -> List[Dict[str, Any]]:
        """
        Obtiene todas las órdenes (abiertas y cerradas).
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            order_id: ID de la orden
            start_time: Tiempo de inicio en milisegundos
            end_time: Tiempo de fin en milisegundos
            limit: Número máximo de órdenes a obtener
            
        Returns:
            Lista de todas las órdenes
        """
        params = {'symbol': symbol, 'limit': limit}
        
        if order_id:
            params['orderId'] = str(order_id)
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
            
        response = self._request('GET', '/v3/allOrders', params, signed=True)
        return response if isinstance(response, list) else []
    
    def get_my_trades(self, symbol: str, start_time: Optional[int] = None, 
                     end_time: Optional[int] = None, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Obtiene las operaciones realizadas por el usuario.
        
        Args:
            symbol: Par de trading
            start_time: Marca de tiempo inicial (milisegundos)
            end_time: Marca de tiempo final (milisegundos)
            limit: Número máximo de operaciones a devolver (máx. 1000)
            
        Returns:
            Lista de operaciones del usuario
        """
        params = {'symbol': symbol, 'limit': limit}
        if start_time: params['startTime'] = start_time
        if end_time: params['endTime'] = end_time
        response = self._request('GET', '/v3/myTrades', params, signed=True)
        return response if isinstance(response, list) else []
    
    # Métodos de WebSocket
    
    def _on_ws_message(self, ws, message, callback):
        """Maneja mensajes recibidos por WebSocket."""
        try:
            data = json.loads(message)
            callback(data)
        except Exception as e:
            logger.error(f"Error procesando mensaje WebSocket: {str(e)}")
    
    def _on_ws_error(self, ws, error):
        """Maneja errores de WebSocket."""
        logger.error(f"Error en WebSocket: {str(error)}")
    
    def _on_ws_close(self, ws, close_status_code, close_msg):
        """Maneja cierre de conexión WebSocket."""
        logger.info(f"WebSocket cerrado: {close_status_code} - {close_msg}")
        # Intentar reconectar
        stream_id = None
        for sid, connection in self.ws_connections.items():
            if connection == ws:
                stream_id = sid
                break
        
        if stream_id:
            logger.info(f"Reconectando WebSocket para stream {stream_id}")
            self._reconnect_websocket(stream_id)
    
    def _on_ws_open(self, ws):
        """Maneja apertura de conexión WebSocket."""
        logger.info("WebSocket conectado")
    
    def _reconnect_websocket(self, stream_id):
        """Reconecta un WebSocket después de un cierre."""
        if stream_id in self.ws_connections:
            callback = self.ws_callbacks.get(stream_id)
            if callback:
                self.subscribe_to_stream(stream_id, callback)
    
    def subscribe_to_stream(self, stream_id: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Suscribe a un stream de datos.
        
        Args:
            stream_id: ID del stream (ej. 'btcusdt@trade')
            callback: Función a llamar con los datos recibidos
        """
        if stream_id in self.ws_connections:
            logger.warning(f"Ya suscrito al stream {stream_id}")
            return
        
        # Crear WebSocket
        ws = WebSocketApp(
            f"{self.ws_url}/{stream_id}",
            on_message=lambda ws, msg: self._on_ws_message(ws, msg, callback),
            on_error=self._on_ws_error,
            on_close=self._on_ws_close,
            on_open=self._on_ws_open
        )
        
        # Guardar callback para reconexión
        self.ws_callbacks[stream_id] = callback
        
        # Iniciar WebSocket en un hilo separado
        thread = threading.Thread(target=ws.run_forever)
        thread.daemon = True
        thread.start()
        
        # Guardar conexión y thread
        self.ws_connections[stream_id] = ws
        self.ws_threads[stream_id] = thread
        
        logger.info(f"Suscrito al stream {stream_id}")
    
    def subscribe_to_ticker(self, symbol: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Suscribe a actualizaciones de ticker.
        
        Args:
            symbol: Par de trading (ej. 'btcusdt')
            callback: Función a llamar con los datos recibidos
        """
        stream_id = f"{symbol.lower()}@ticker"
        self.subscribe_to_stream(stream_id, callback)
    
    def subscribe_to_trades(self, symbol: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Suscribe a trades en tiempo real.
        
        Args:
            symbol: Par de trading (ej. 'btcusdt')
            callback: Función a llamar con los datos recibidos
        """
        stream_id = f"{symbol.lower()}@trade"
        self.subscribe_to_stream(stream_id, callback)
    
    def subscribe_to_klines(self, symbol: str, interval: str, 
                          callback: Callable[[Dict[str, Any]], None]):
        """
        Suscribe a actualizaciones de velas.
        
        Args:
            symbol: Par de trading (ej. 'btcusdt')
            interval: Intervalo de tiempo (ej. '1m', '1h', '1d')
            callback: Función a llamar con los datos recibidos
        """
        stream_id = f"{symbol.lower()}@kline_{interval}"
        self.subscribe_to_stream(stream_id, callback)
    
    def unsubscribe_from_stream(self, stream_id: str):
        """
        Cancela la suscripción a un stream.
        
        Args:
            stream_id: ID del stream
        """
        if stream_id in self.ws_connections:
            self.ws_connections[stream_id].close()
            del self.ws_connections[stream_id]
            del self.ws_threads[stream_id]
            logger.info(f"Desuscrito del stream {stream_id}")
    
    def close_all_connections(self):
        """Cierra todas las conexiones WebSocket."""
        for stream_id in list(self.ws_connections.keys()):
            self.unsubscribe_from_stream(stream_id)
        logger.info("Todas las conexiones WebSocket cerradas")
    
    def __del__(self):
        """Destructor que cierra todas las conexiones."""
        self.close_all_connections()

    # --- Methods from ExchangeInterface requiring implementation ---

    def get_ticker_price(self, symbol: str) -> Decimal:
        """Get the current price for a trading pair (Implementation from Interface)."""
        # Reuse existing get_symbol_price logic
        try:
            price_info = self.get_symbol_price(symbol)
            return Decimal(price_info['price'])
        except (APIError, KeyError, ValueError) as e:
            logger.error(f"Error getting ticker price for {symbol}: {e}")
            # Re-raise as a generic APIError or a more specific custom error if defined
            raise APIError(f"Could not retrieve ticker price for {symbol}: {e}")

    # Note: get_balance is already implemented with a slightly different signature 
    # (accepts optional asset, returns Dict or List). 
    # If exact interface compliance is needed, an adapter method might be required.
    # Or, adjust the interface definition if this implementation is preferred.

    def get_order_status(self, order_id: str, symbol: str) -> OrderInfo:
        """Get order status."""
        order = self.get_order(symbol, order_id=int(order_id))
        return OrderInfo(
            order_id=str(order['orderId']),
            symbol=order['symbol'],
            order_type=order['type'],
            side=order['side'],
            amount=Decimal(order['origQty']),
            price=Decimal(order['price']),
            status=order['status'],
            created_at=datetime.fromtimestamp(order['time'] / 1000),
            updated_at=datetime.fromtimestamp(order['updateTime'] / 1000),
            filled_amount=Decimal(order['executedQty']),
            average_price=Decimal(order['price'])
        )

    def _parse_order_book(self, entries: List[List[str]], limit: int = 100) -> List[OrderBookEntry]:
        """Parse order book entries."""
        result = []
        for entry in entries[:limit]:
            price, amount = Decimal(entry[0]), Decimal(entry[1])
            result.append(OrderBookEntry(
                price=price,
                amount=amount,
                timestamp=datetime.utcnow()
            ))
        return result

    async def get_order_book(self, symbol: str, limit: int = 100) -> Tuple[List[OrderBookEntry], List[OrderBookEntry]]:
        """Get order book for a symbol."""
        endpoint = '/v3/depth'
        params = {
            'symbol': symbol.upper(),
            'limit': limit
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}{endpoint}", params=params) as response:
                response.raise_for_status()
                data = await response.json()
                bids = self._parse_order_book(data['bids'], limit)
                asks = self._parse_order_book(data['asks'], limit)
                return bids, asks

    def get_trading_fees(self, symbol: str) -> Dict[str, Decimal]:
        """Get the trading fees for a specific trading pair (Placeholder)."""
        # Requires calling /sapi/v1/asset/tradeFee endpoint and parsing the result.
        logger.warning("get_trading_fees implementation is missing.")
        raise NotImplementedError("get_trading_fees is not yet implemented in BinanceAPI")

    def _convert_timestamp(self, timestamp: int) -> datetime:
        """Convert millisecond timestamp to datetime."""
        return datetime.fromtimestamp(timestamp / 1000.0)

    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trades for a symbol."""
        url = f"{self.base_url}/api/v3/trades"
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()

    def get_24h_ticker_stats(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Obtiene estadísticas de 24 horas para un símbolo.
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            
        Returns:
            Diccionario con estadísticas de 24h incluyendo:
            - Precio de apertura
            - Precio más alto
            - Precio más bajo
            - Volumen
            - Cambio de precio
            - Cambio de precio porcentual
            - Precio promedio ponderado por volumen
        """
        try:
            return self._request('GET', '/v3/ticker/24hr', {'symbol': symbol})
        except APIError as e:
            logger.error(f"Error obteniendo estadísticas de 24h para {symbol}: {str(e)}")
            raise

    def get_depth(self, symbol: str = "BTCUSDT", limit: int = 100) -> Dict[str, Any]:
        """
        Obtiene el libro de órdenes completo para un símbolo.
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            limit: Número de niveles de profundidad (5, 10, 20, 50, 100, 500, 1000, 5000)
            
        Returns:
            Diccionario con el libro de órdenes incluyendo:
            - bids: Lista de órdenes de compra [precio, cantidad]
            - asks: Lista de órdenes de venta [precio, cantidad]
        """
        try:
            return self._request('GET', '/v3/depth', {'symbol': symbol, 'limit': limit})
        except APIError as e:
            logger.error(f"Error obteniendo profundidad del libro para {symbol}: {str(e)}")
            raise

    def get_aggregated_trades(self, symbol: str = "BTCUSDT", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene trades agregados recientes.
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            limit: Número máximo de trades a obtener (máx. 1000)
            
        Returns:
            Lista de trades agregados con información de:
            - Precio
            - Cantidad
            - Tiempo
            - ID del trade
            - Es comprador fabricante
        """
        try:
            response = self._request('GET', '/v3/aggTrades', {'symbol': symbol, 'limit': limit})
            return response if isinstance(response, list) else []
        except APIError as e:
            logger.error(f"Error obteniendo trades agregados para {symbol}: {str(e)}")
            raise

    def get_average_price(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Obtiene el precio promedio de un símbolo.
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            
        Returns:
            Diccionario con el precio promedio y el número de minutos
        """
        try:
            return self._request('GET', '/v3/avgPrice', {'symbol': symbol})
        except APIError as e:
            logger.error(f"Error obteniendo precio promedio para {symbol}: {str(e)}")
            raise

    def get_best_bid_ask(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Obtiene el mejor bid y ask para un símbolo.
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            
        Returns:
            Diccionario con el mejor bid y ask
        """
        try:
            return self._request('GET', '/v3/ticker/bookTicker', {'symbol': symbol})
        except APIError as e:
            logger.error(f"Error obteniendo mejor bid/ask para {symbol}: {str(e)}")
            raise

    def get_historical_trades(self, symbol: str = "BTCUSDT", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene el histórico de trades.
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            limit: Número máximo de trades a obtener (máx. 1000)
            
        Returns:
            Lista de trades históricos
        """
        try:
            response = self._request('GET', '/v3/historicalTrades', {'symbol': symbol, 'limit': limit})
            return response if isinstance(response, list) else []
        except APIError as e:
            logger.error(f"Error obteniendo histórico de trades para {symbol}: {str(e)}")
            raise

    def get_exchange_rules(self) -> Dict[str, Any]:
        """
        Obtiene las reglas del exchange, filtros y límites.
        
        Returns:
            Diccionario con las reglas del exchange
        """
        try:
            return self._request('GET', '/v3/exchangeInfo')
        except APIError as e:
            logger.error(f"Error obteniendo reglas del exchange: {str(e)}")
            raise

    def subscribe_to_depth(self, symbol: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Suscribe a actualizaciones del libro de órdenes en tiempo real.
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            callback: Función a llamar con las actualizaciones
        """
        stream_id = f"{symbol.lower()}@depth"
        self.subscribe_to_stream(stream_id, callback)

    def subscribe_to_account_updates(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Suscribe a actualizaciones de la cuenta en tiempo real.
        
        Args:
            callback: Función a llamar con las actualizaciones
        """
        if not self.api_key or not self.api_secret:
            raise AuthenticationError("Se requieren credenciales API para suscribirse a actualizaciones de cuenta")
        
        stream_id = f"{self.api_key}@account"
        self.subscribe_to_stream(stream_id, callback)

    def get_futures_open_interest(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Obtiene el Open Interest para futuros.
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            
        Returns:
            Diccionario con el Open Interest incluyendo:
            - symbol: Par de trading
            - openInterest: Cantidad total de contratos abiertos
            - time: Marca de tiempo
        """
        try:
            return self._request('GET', '/fapi/v1/openInterest', {'symbol': symbol}, futures=True)
        except APIError as e:
            logger.error(f"Error obteniendo Open Interest para {symbol}: {str(e)}")
            raise

    def get_futures_ticker(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Obtiene el ticker de futuros para un símbolo.
        
        Args:
            symbol: Par de trading (ej. 'BTCUSDT')
            
        Returns:
            Diccionario con información del ticker de futuros
        """
        try:
            return self._request('GET', '/fapi/v1/ticker/24hr', {'symbol': symbol}, futures=True)
        except APIError as e:
            logger.error(f"Error obteniendo ticker de futuros para {symbol}: {str(e)}")
            raise

    async def subscribe_to_order_book(self, symbol: str, callback: Callable) -> None:
        """
        Subscribe to real-time order book updates.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            callback: Function to be called with order book updates. The callback will receive
                     a tuple of (bids, asks) where each is a list of OrderBookEntry objects.
        """
        def process_depth_update(msg: Dict[str, Any]) -> None:
            try:
                current_time = datetime.fromtimestamp(time.time())
                bids = [
                    OrderBookEntry(
                        price=Decimal(str(price)),
                        amount=Decimal(str(amount)),
                        timestamp=current_time
                    )
                    for price, amount in msg.get('b', [])
                ]
                
                asks = [
                    OrderBookEntry(
                        price=Decimal(str(price)),
                        amount=Decimal(str(amount)),
                        timestamp=current_time
                    )
                    for price, amount in msg.get('a', [])
                ]
                
                callback((bids, asks))
                
            except Exception as e:
                logger.error(f"Error processing order book update: {str(e)}")
        
        # Convert symbol to lowercase for WebSocket stream
        stream_id = f"{symbol.lower()}@depth@100ms"  # Using 100ms updates for more frequent data
        self.subscribe_to_stream(stream_id, process_depth_update)

def test_bitcoin_data_retrieval():
    """
    Prueba la funcionalidad de recuperación de datos de Bitcoin.
    """
    # Inicializar API
    api = BinanceAPI()
    
    try:
        # Probar funcionalidad spot
        print("\nProbando funcionalidad spot...")
        ticker = api.get_24h_ticker_stats("BTCUSDT")
        print(f"Ticker BTCUSDT: {ticker}")
        
        orderbook = api.get_depth("BTCUSDT")
        print(f"Order Book BTCUSDT (primeras 5 órdenes):")
        print(f"Bids: {orderbook['bids'][:5]}")
        print(f"Asks: {orderbook['asks'][:5]}")
        
        trades = api.get_historical_trades("BTCUSDT")
        print(f"Trades recientes (primeros 5): {trades[:5]}")
        
        klines = api.get_klines("BTCUSDT", "1h", limit=5)
        print(f"Klines (últimas 5 velas): {klines}")
        
        avg_price = api.get_average_price("BTCUSDT")
        print(f"Precio promedio: {avg_price}")
        
        best_price = api.get_best_bid_ask("BTCUSDT")
        print(f"Mejor precio - Bid: {best_price['bidPrice']}, Ask: {best_price['askPrice']}")
        
        # Probar funcionalidad de futuros
        print("\nProbando funcionalidad de futuros...")
        futures_oi = api.get_futures_open_interest("BTCUSDT")
        print(f"Open Interest de futuros: {futures_oi}")
        
        futures_ticker = api.get_futures_ticker("BTCUSDT")
        print(f"Ticker de futuros: {futures_ticker}")
        
        print("\nTodas las pruebas completadas exitosamente!")
        
    except Exception as e:
        print(f"Error durante las pruebas: {str(e)}")
        raise

if __name__ == "__main__":
    test_bitcoin_data_retrieval()
