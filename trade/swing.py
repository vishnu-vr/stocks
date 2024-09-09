import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import time
import os

# Function to calculate EMA
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

# Function to calculate SMA
def sma(series, span):
    return series.rolling(window=span).mean()

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

# Function to fetch stock data
def get_stock_data(ticker):
    interval = '1d'  # 1 day interval
    data = yf.download(ticker, period='6mo', interval=interval)  # Adjust the period as needed
    # Convert index to timezone-aware datetime
    data.index = data.index.tz_localize('Asia/Kolkata')
    return data

# Function to read Nifty stocks from a CSV file and add .NS suffix
def fetch_nifty_stocks(file_path):
    df = pd.read_csv(file_path)
    # Assuming the CSV file has a column named 'Symbol' containing the stock symbols
    nifty_stocks = df['Symbol'].apply(lambda x: x.strip() + '.NS').tolist()
    return nifty_stocks

def main_driver(ticker, percentage):
    data = get_stock_data(ticker)

    # Calculate MACD
    data = calculate_macd(data)

    # Calculate RSI
    data = calculate_rsi(data)

    # Calculate additional indicators
    data['EMA_44'] = ema(data['Close'], 44)  # Calculate 44-period EMA
    data['SMA_10'] = sma(data['Close'], 10)  # Calculate 10-period SMA
    data['SMA_20'] = sma(data['Close'], 20)  # Calculate 20-period SMA

    # Check conditions on the latest row
    latest_row = data.iloc[-1]

    # Define conditions
    conditions = [
        latest_row['RSI'] < 60,  # Condition 1: RSI is below 60
        latest_row['MACD'] > latest_row['Signal_Line'],  # Condition 2: MACD line is above signal line
        # latest_row['MACD'] < 0,  # Condition 3: MACD line is under the histogram
        latest_row['Close'] > latest_row['EMA_44'],  # Condition 4: Above 44 EMA
        latest_row['SMA_10'] > latest_row['SMA_20']  # Condition 5: 10 SMA greater than 20 SMA
    ]

    # Calculate number of conditions to meet
    num_conditions = len(conditions)
    num_conditions_to_meet = int(num_conditions * (percentage / 100))

    # Check if MACD condition is met
    macd_condition_met = conditions[1] and True  #conditions[2]  # MACD conditions
    if not macd_condition_met:
        print(f"MACD conditions not met for {ticker}. Skipping.")
        return

    # Count how many conditions are met including MACD
    conditions_met_count = sum(conditions)

    if conditions_met_count >= num_conditions_to_meet:
        data.index = data.index.tz_localize(None)
        
        # Save to Excel if conditions are met
        data.to_excel(f'delete_me\\{ticker}.xlsx', index=True)
        print(f"Conditions met for {ticker}. Data saved to Excel.")
    else:
        print(f"Conditions not met for {ticker}. Skipping.")

if __name__ == "__main__":
    # Specify the path to your text file with Nifty stocks
    nifty_stocks_file = 'ind_nifty500list.csv'
    nifty_stocks = fetch_nifty_stocks(nifty_stocks_file)
    
    # Specify the percentage of conditions to be met
    percentage = 100  # Adjust this percentage as needed

    for ticker in nifty_stocks:
        print(f"Processing {ticker}...")
        try:
            main_driver(ticker, percentage)
        except Exception as e:
            print(f"Failed for {ticker}: {e}")
