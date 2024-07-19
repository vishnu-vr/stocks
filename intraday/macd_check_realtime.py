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

# Function to calculate RSI
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    return data

# Function to check for MACD crossover and mark buy/sell signals
def check_macd_signals(data):
    macd_signals = [''] * len(data)
    for i in range(1, len(data)):
        if data['MACD'].iloc[i] > data['Signal_Line'].iloc[i] and data['MACD'].iloc[i-1] <= data['Signal_Line'].iloc[i-1]:
            if data['MACD'].iloc[i] < 0 and data['Signal_Line'].iloc[i] < 0:
                macd_signals[i] = 'Positive_Crossover'
    return macd_signals

# Function to check RSI conditions
def check_rsi_signals(data):
    rsi_signals = [''] * len(data)
    for i in range(1, len(data)):
        if data['RSI'].iloc[i] < 70:
            rsi_signals[i] = 'Below_70'
    return rsi_signals

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

    # Calculate RSI
    data = calculate_rsi(data)

    # Check for MACD crossovers and mark Buy/Sell signals
    data['MACD_Signal'] = check_macd_signals(data)

    # Check for RSI conditions and mark Buy/Sell signals
    data['RSI_Signal'] = check_rsi_signals(data)

    # Determine final buy/sell signals based on both MACD and RSI
    data['Final_Signal'] = [''] * len(data)
    previous_signal = 'Sell'
    last_buy_price = None
    for i in range(1, len(data)):
        if previous_signal == 'Sell' and data['MACD_Signal'].iloc[i] == 'Positive_Crossover' and data['RSI_Signal'].iloc[i] == 'Below_70':
            data['Final_Signal'].iloc[i] = 'Buy'
            last_buy_price = data['Close'].iloc[i]
            previous_signal = 'Buy'
        elif previous_signal == 'Buy':
            if ((data['High'].iloc[i] - last_buy_price) / last_buy_price) >= 0.002 or \
               ((data['Low'].iloc[i] - last_buy_price) / last_buy_price) >= 0.002 or \
               ((data['Open'].iloc[i] - last_buy_price) / last_buy_price) >= 0.002 or \
               ((data['Close'].iloc[i] - last_buy_price) / last_buy_price) >= 0.002:
                last_buy_price = None
                data['Final_Signal'].iloc[i] = 'Sell'
                previous_signal = 'Sell'

    # Convert datetime index to timezone-naive
    data.index = data.index.tz_localize(None)

    # Write the DataFrame to an Excel file
    data.to_excel('macd_rsi_signals.xlsx', index=True)

    print("Data with Buy/Sell signals has been written to macd_rsi_signals.xlsx")
