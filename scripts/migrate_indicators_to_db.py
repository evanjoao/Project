import os
import json
import csv
import psycopg2
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
import getpass

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'trading_db'),
    'user': os.getenv('DB_USERNAME', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '@Elreyfriki007'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

def connect_to_db():
    """Establecer conexión con la base de datos"""
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port']
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error al conectar a la base de datos: {str(e)}")
        raise

def migrate_technical_indicators(conn):
    """Migrar indicadores técnicos"""
    cursor = conn.cursor()
    
    # Migrar RSI
    with open('data/processed/indicators/technical/rsi_daily.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT INTO technical_indicators (timestamp, symbol, indicator_type, interval, values)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (timestamp, symbol, indicator_type, interval) 
                DO UPDATE SET values = EXCLUDED.values
            """, (
                datetime.strptime(row['timestamp'], '%Y-%m-%d'),
                row['symbol'],
                'RSI',
                '1d',
                json.dumps({'rsi_value': float(row['rsi_value'])})
            ))
    
    # Migrar MACD
    with open('data/processed/indicators/technical/macd_4h.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT INTO technical_indicators (timestamp, symbol, indicator_type, interval, values)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (timestamp, symbol, indicator_type, interval) 
                DO UPDATE SET values = EXCLUDED.values
            """, (
                datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S'),
                row['symbol'],
                'MACD',
                '4h',
                json.dumps({
                    'macd_line': float(row['macd_line']),
                    'signal_line': float(row['signal_line']),
                    'histogram': float(row['histogram'])
                })
            ))
    
    # Migrar Bollinger Bands
    with open('data/processed/indicators/technical/bollinger_bands_1h.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT INTO technical_indicators (timestamp, symbol, indicator_type, interval, values)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (timestamp, symbol, indicator_type, interval) 
                DO UPDATE SET values = EXCLUDED.values
            """, (
                datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S'),
                row['symbol'],
                'BOLLINGER_BANDS',
                '1h',
                json.dumps({
                    'upper_band': float(row['upper_band']),
                    'middle_band': float(row['middle_band']),
                    'lower_band': float(row['lower_band']),
                    'price': float(row['price'])
                })
            ))
    
    conn.commit()

def migrate_sentiment_indicators(conn):
    """Migrar indicadores de sentimiento"""
    cursor = conn.cursor()
    
    # Migrar social sentiment
    with open('data/processed/indicators/sentiment/social_sentiment_daily.json', 'r') as f:
        data = json.load(f)
        for timestamp, values in data.items():
            cursor.execute("""
                INSERT INTO sentiment_indicators (timestamp, source, values)
                VALUES (%s, %s, %s)
                ON CONFLICT (timestamp, source) 
                DO UPDATE SET values = EXCLUDED.values
            """, (
                datetime.strptime(timestamp, '%Y-%m-%d'),
                'social',
                json.dumps(values)
            ))
    
    # Migrar fear and greed index
    with open('data/processed/indicators/sentiment/fear_greed_index.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT INTO sentiment_indicators (timestamp, source, values)
                VALUES (%s, %s, %s)
                ON CONFLICT (timestamp, source) 
                DO UPDATE SET values = EXCLUDED.values
            """, (
                datetime.strptime(row['timestamp'], '%Y-%m-%d'),
                'fear_greed',
                json.dumps({
                    'value': float(row['value']),
                    'classification': row['classification'],
                    'btc_price': float(row['btc_price']),
                    'btc_volume': float(row['btc_volume']),
                    'dominance': float(row['dominance'])
                })
            ))
    
    conn.commit()

def migrate_whale_indicators(conn):
    """Migrar indicadores de whale"""
    cursor = conn.cursor()
    
    # Migrar large transfers
    with open('data/processed/indicators/whale/large_transfers_daily.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT INTO whale_indicators (timestamp, indicator_type, values)
                VALUES (%s, %s, %s)
                ON CONFLICT (timestamp, indicator_type) 
                DO UPDATE SET values = EXCLUDED.values
            """, (
                datetime.strptime(row['timestamp'], '%Y-%m-%d'),
                'large_transfers',
                json.dumps({
                    'from_address': row['from_address'],
                    'to_address': row['to_address'],
                    'amount_btc': float(row['amount_btc']),
                    'value_usd': float(row['value_usd']),
                    'type': row['type']
                })
            ))
    
    # Migrar whale accumulation
    with open('data/processed/indicators/whale/whale_accumulation.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT INTO whale_indicators (timestamp, indicator_type, values)
                VALUES (%s, %s, %s)
                ON CONFLICT (timestamp, indicator_type) 
                DO UPDATE SET values = EXCLUDED.values
            """, (
                datetime.strptime(row['timestamp'], '%Y-%m-%d'),
                'accumulation',
                json.dumps({
                    'address': row['address'],
                    'balance_change': float(row['balance_change']),
                    'current_balance': float(row['current_balance']),
                    'percentage_change': float(row['percentage_change']),
                    'type': row['type']
                })
            ))
    
    conn.commit()

def migrate_market_indicators(conn):
    """Migrar indicadores de mercado"""
    cursor = conn.cursor()
    
    # Migrar volatility metrics
    with open('data/processed/indicators/market/volatility_metrics.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT INTO market_indicators (timestamp, symbol, indicator_type, values)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (timestamp, symbol, indicator_type) 
                DO UPDATE SET values = EXCLUDED.values
            """, (
                datetime.strptime(row['timestamp'], '%Y-%m-%d'),
                row['symbol'],
                'volatility',
                json.dumps({
                    'daily_volatility': float(row['daily_volatility']),
                    'weekly_volatility': float(row['weekly_volatility']),
                    'monthly_volatility': float(row['monthly_volatility']),
                    'atr_14': float(row['atr_14']),
                    'true_range': float(row['true_range'])
                })
            ))
    
    # Migrar liquidity indicators
    with open('data/processed/indicators/market/liquidity_indicators.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT INTO market_indicators (timestamp, symbol, indicator_type, values)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (timestamp, symbol, indicator_type) 
                DO UPDATE SET values = EXCLUDED.values
            """, (
                datetime.strptime(row['timestamp'], '%Y-%m-%d'),
                row['symbol'],
                'liquidity',
                json.dumps({
                    'order_book_depth': float(row['order_book_depth']),
                    'spread_percentage': float(row['spread_percentage']),
                    'volume_24h': float(row['volume_24h']),
                    'market_cap': float(row['market_cap']),
                    'dominance': float(row['dominance'])
                })
            ))
    
    conn.commit()

def main():
    """Función principal de migración"""
    try:
        conn = connect_to_db()
        print("Conexión establecida con la base de datos")
        
        print("Migrando indicadores técnicos...")
        migrate_technical_indicators(conn)
        
        print("Migrando indicadores de sentimiento...")
        migrate_sentiment_indicators(conn)
        
        print("Migrando indicadores de whale...")
        migrate_whale_indicators(conn)
        
        print("Migrando indicadores de mercado...")
        migrate_market_indicators(conn)
        
        print("Migración completada exitosamente")
        
    except Exception as e:
        print(f"Error durante la migración: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main() 