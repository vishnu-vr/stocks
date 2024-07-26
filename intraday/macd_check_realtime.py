import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import time
from plyer import notification
import os
import sys

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

# Function to calculate ATR
def calculate_atr(data, period=14):
    high_low = data['High'] - data['Low']
    high_close = (data['High'] - data['Close'].shift()).abs()
    low_close = (data['Low'] - data['Close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr

# Function to calculate Super Trend
def calculate_super_trend(data, period=14, multiplier=3):
    atr = calculate_atr(data, period)
    data['Basic_Upper_Band'] = (data['High'] + data['Low']) / 2 + (multiplier * atr)
    data['Basic_Lower_Band'] = (data['High'] + data['Low']) / 2 - (multiplier * atr)
    
    data['Final_Upper_Band'] = data['Basic_Upper_Band']
    data['Final_Lower_Band'] = data['Basic_Lower_Band']
    
    for i in range(1, len(data)):
        if data['Close'].iloc[i-1] > data['Final_Upper_Band'].iloc[i-1]:
            data.loc[data.index[i], 'Final_Upper_Band'] = min(data['Basic_Upper_Band'].iloc[i], data['Final_Upper_Band'].iloc[i-1])
        else:
            data.loc[data.index[i], 'Final_Upper_Band'] = data['Basic_Upper_Band'].iloc[i]

        if data['Close'].iloc[i-1] < data['Final_Lower_Band'].iloc[i-1]:
            data.loc[data.index[i], 'Final_Lower_Band'] = max(data['Basic_Lower_Band'].iloc[i], data['Final_Lower_Band'].iloc[i-1])
        else:
            data.loc[data.index[i], 'Final_Lower_Band'] = data['Basic_Lower_Band'].iloc[i]
            
    data['Super_Trend'] = 0.0
    for i in range(1, len(data)):
        if data['Close'].iloc[i-1] <= data['Final_Upper_Band'].iloc[i-1] and data['Close'].iloc[i] > data['Final_Upper_Band'].iloc[i]:
            data.loc[data.index[i], 'Super_Trend'] = data['Final_Lower_Band'].iloc[i]
        elif data['Close'].iloc[i-1] >= data['Final_Lower_Band'].iloc[i-1] and data['Close'].iloc[i] < data['Final_Lower_Band'].iloc[i]:
            data.loc[data.index[i], 'Super_Trend'] = data['Final_Upper_Band'].iloc[i]
        else:
            data.loc[data.index[i], 'Super_Trend'] = data['Super_Trend'].iloc[i-1]

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
        if data['RSI'].iloc[i] < 40:
            rsi_signals[i] = 'Below_40'
    return rsi_signals

# Function to fetch stock data
def get_stock_data(ticker):
    interval = '1m'  # 1 minute interval
    data = yf.download(ticker, period='1d', interval=interval)
    # Convert index to timezone-aware datetime
    data.index = data.index.tz_convert('Asia/Kolkata')
    return data

def prompt_user_buy(price, target_price):
    print(f'Buy this stock now at {price}! Target price: {target_price:.2f}')
    notification.notify(
        title='Buy Alert',
        message=f'Buy this stock now at {price}! Target price: {target_price:.2f}',
        app_name='Stock Alert',
        timeout=20  # Duration in seconds
    )

def live_day_run(data, i, price):
    # Get the current system timestamp and make it timezone-aware
    current_time = datetime.now(pytz.timezone('Asia/Kolkata'))

    # Get the timestamp of the current data point and ensure it's timezone-aware
    data_timestamp = data.index[i].to_pydatetime().astimezone(pytz.timezone('Asia/Kolkata'))

    time_difference = current_time - data_timestamp

    # Calculate the target price with a 0.2% increase
    target_price = price * 1.002

    # Check if the time difference is less than or equal to 2 minutes
    if abs(time_difference) <= timedelta(minutes=2):
        prompt_user_buy(price, target_price)

def main_driver(live_day, ticker):
    # ticker = 'ANANTRAJ.NS'
    data = get_stock_data(ticker)

    # Calculate MACD
    data = calculate_macd(data)

    # Calculate RSI
    data = calculate_rsi(data)

    # Calculate Super Trend
    # data = calculate_super_trend(data)

    # Check for MACD crossovers and mark Buy/Sell signals
    data['MACD_Signal'] = check_macd_signals(data)

    # Check for RSI conditions and mark Buy/Sell signals
    data['RSI_Signal'] = check_rsi_signals(data)

    # Determine final buy/sell signals based on both MACD and RSI
    data['Final_Signal'] = [''] * len(data)
    previous_signal = 'Sell'
    last_buy_price = None
    for i in range(1, len(data)):
        if previous_signal == 'Sell' and data['MACD_Signal'].iloc[i] == 'Positive_Crossover' and data['RSI_Signal'].iloc[i] == 'Below_40':
            data.loc[data.index[i], 'Final_Signal'] = 'Buy'
            last_buy_price = data['Close'].iloc[i]
            previous_signal = 'Buy'

            if live_day:
                live_day_run(data, i, last_buy_price)

        elif previous_signal == 'Buy':
            if ((data['High'].iloc[i] - last_buy_price) / last_buy_price) >= 0.002 or \
               ((data['Low'].iloc[i] - last_buy_price) / last_buy_price) >= 0.002 or \
               ((data['Open'].iloc[i] - last_buy_price) / last_buy_price) >= 0.002 or \
               ((data['Close'].iloc[i] - last_buy_price) / last_buy_price) >= 0.002:
                last_buy_price = None
                data.loc[data.index[i], 'Final_Signal'] = 'Sell'
                previous_signal = 'Sell'

    if not live_day:
        # Convert datetime index to timezone-naive
        data.index = data.index.tz_localize(None)

        # Write the DataFrame to an Excel file
        data.to_excel(f'macd_rsi_supertrend_signals_{ticker}.xlsx', index=True)

        print("Data with Buy/Sell signals has been written to macd_rsi_supertrend_signals.xlsx")

if __name__ == "__main__":
    ticker = sys.argv[1]#'STCINDIA.NS'

    # Set the console window title to the ticker name
    # ctypes.windll.user32.SetConsoleTitleA(ticker)
    # os.system(f'title {ticker}')
    live_day = False
    
    if live_day:
        while True:
            main_driver(live_day, ticker)
            time.sleep(30)  # Delay for 1 minute
    else:
        main_driver(live_day, ticker)
