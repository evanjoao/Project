import os
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL

# Load your Binance API key and secret from environment variables
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

# Initialize the Binance client
client = Client(API_KEY, API_SECRET)

def place_order(symbol, side, quantity):
    """
    Place a market order on Binance.

    :param symbol: Trading pair symbol (e.g., 'BTCUSDT')
    :param side: Order side ('BUY' or 'SELL')
    :param quantity: Quantity to trade
    """
    try:
        order = client.create_order(
            symbol=symbol,
            side=SIDE_BUY if side.upper() == 'BUY' else SIDE_SELL,
            type='MARKET',
            quantity=quantity
        )
        print("Order placed successfully:", order)
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    # Example usage
    trading_pair = input("Enter the trading pair (e.g., BTCUSDT): ")
    order_side = input("Enter the order side (BUY/SELL): ")
    trade_quantity = float(input("Enter the quantity to trade: "))

    place_order(trading_pair, order_side, trade_quantity)