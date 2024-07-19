import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import time
import os

# Function to calculate MACD
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def calculate_macd(data, slow=26, fast=12, signal=9):
    data['EMA_fast'] = ema(data['Close'], fast)
    data['EMA_slow'] = ema(data['Close'], slow)
    data['MACD'] = data['EMA_fast'] - data['EMA_slow']
    data['Signal_Line'] = ema(data['MACD'], signal)
    data['Histogram'] = data['MACD'] - data['Signal_Line']
    return data

# Function to check for MACD crossover
def check_macd_crossover(data):
    crossovers = []
    for i in range(1, len(data)):
        if data['MACD'].iloc[i] > data['Signal_Line'].iloc[i] and data['MACD'].iloc[i-1] <= data['Signal_Line'].iloc[i-1]:
            if data['MACD'].iloc[i] < 0 and data['Signal_Line'].iloc[i] < 0:
                crossovers.append(data.index[i])
    return crossovers

# Function to check for negative MACD crossover above the histogram
def check_macd_negative_crossover(data):
    crossovers = []
    for i in range(1, len(data)):
        if data['MACD'].iloc[i] < data['Signal_Line'].iloc[i] and data['MACD'].iloc[i-1] >= data['Signal_Line'].iloc[i-1]:
            if data['MACD'].iloc[i] > 0 and data['Signal_Line'].iloc[i] > 0:
                crossovers.append(data.index[i])
    return crossovers

# Define the ticker and the monitoring period
ticker = 'TTML.NS'
interval = '1m'  # 1 minute interval
monitoring_duration = timedelta(hours=6)  # Monitor for 6 hours
end_time = datetime.now() + monitoring_duration

# Real-time monitoring
last_printed_crossover = None

while datetime.now() < end_time:
    # Fetch recent intraday stock data
    data = yf.download(ticker, period='1d', interval=interval)
    
    # Convert index to timezone-aware datetime
    data.index = data.index.tz_convert('Asia/Kolkata')
    
    # Calculate MACD
    data = calculate_macd(data)
    
    # Check for MACD crossover
    crossovers = check_macd_crossover(data)
    negative_crossovers = check_macd_negative_crossover(data)
    
    os.system('cls')

    # Print crossovers
    for crossover in crossovers:
        print(f"New MACD crossover detected at {crossover}")
        
    for negative_crossover in negative_crossovers:
        print(f"New MACD negative crossover detected at {negative_crossover}")
    
    # Wait for a minute before fetching the data again
    time.sleep(60)
