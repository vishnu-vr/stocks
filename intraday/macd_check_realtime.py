import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz

# Function to calculate EMA
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

# Function to calculate MACD
def calculate_macd(data, slow=26, fast=12, signal=9):
    data['EMA_fast'] = ema(data['Close'], fast)
    data['EMA_slow'] = ema(data['Close'], slow)
    data['MACD'] = data['EMA_fast'] - data['EMA_slow']
    data['Signal_Line'] = ema(data['MACD'], signal)
    data['Histogram'] = data['MACD'] - data['Signal_Line']
    return data

# Function to check for MACD crossover and mark buy/sell signals
def check_macd_signals(data):
    signals = [''] * len(data)
    last_buy_price = None

    for i in range(1, len(data)):
        if last_buy_price is None and data['MACD'].iloc[i] > data['Signal_Line'].iloc[i] and data['MACD'].iloc[i-1] <= data['Signal_Line'].iloc[i-1]:
            if data['MACD'].iloc[i] < 0 and data['Signal_Line'].iloc[i] < 0:
                signals[i] = 'Buy'
                last_buy_price = data['Close'].iloc[i]
        elif last_buy_price is not None:
            if ((data['High'].iloc[i] - last_buy_price) / last_buy_price) >= 0.002 or \
               ((data['Low'].iloc[i] - last_buy_price) / last_buy_price) >= 0.002 or \
               ((data['Open'].iloc[i] - last_buy_price) / last_buy_price) >= 0.002 or \
               ((data['Close'].iloc[i] - last_buy_price) / last_buy_price) >= 0.002:
                signals[i] = 'Sell'
                last_buy_price = None

    return signals

# Function to fetch stock data
def get_stock_data(ticker):
    interval = '1m'  # 1 minute interval
    data = yf.download(ticker, period='1d', interval=interval)
    # Convert index to timezone-aware datetime
    data.index = data.index.tz_convert('Asia/Kolkata')
    return data

if __name__ == "__main__":
    ticker = 'TTML.NS'
    data = get_stock_data(ticker)

    # Calculate MACD
    data = calculate_macd(data)

    # Check for MACD crossovers and mark Buy/Sell signals
    data['Signal'] = check_macd_signals(data)

    # Convert datetime index to timezone-naive
    data.index = data.index.tz_localize(None)

    # Write the DataFrame to an Excel file
    data.to_excel('macd_signals.xlsx', index=True)

    print("Data with Buy/Sell signals has been written to macd_signals.xlsx")
