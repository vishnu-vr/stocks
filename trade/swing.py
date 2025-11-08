import pandas as pd
import yfinance as yf
import warnings
from multiprocessing import Pool, cpu_count
# This line ignores ALL warnings
warnings.filterwarnings("ignore")

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
# def calculate_rsi(data, window=14):
#     delta = data['Close'].diff()
#     gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
#     loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
#     rs = gain / loss
#     data['RSI'] = 100 - (100 / (1 + rs))
#     return data
# Function to calculate RSI - CORRECTED VERSION
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Use Wilder's smoothing (EMA with alpha = 1/window) instead of SMA
    avg_gain = gain.ewm(alpha=1/window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/window, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))
    return data

# Function to calculate Bollinger Bands
def calculate_bollinger_bands(data, window=20, num_std=2):
    data['BB_Middle'] = sma(data['Close'], window)
    data['BB_Std'] = data['Close'].rolling(window=window).std()
    data['BB_Upper'] = data['BB_Middle'] + num_std * data['BB_Std']
    data['BB_Lower'] = data['BB_Middle'] - num_std * data['BB_Std']
    return data

# Function to calculate ADX
def calculate_adx(data, period=14):
    # Compute true range components
    data['H-L'] = data['High'] - data['Low']
    data['H-Cp'] = abs(data['High'] - data['Close'].shift(1))
    data['L-Cp'] = abs(data['Low'] - data['Close'].shift(1))
    data['TR'] = data[['H-L', 'H-Cp', 'L-Cp']].max(axis=1)

    # Compute directional movements
    data['+DM'] = data['High'].diff()
    data['-DM'] = data['Low'].diff() * -1
    data['+DM'] = data['+DM'].where((data['+DM'] > data['-DM']) & (data['+DM'] > 0), 0.0)
    data['-DM'] = data['-DM'].where((data['-DM'] > data['+DM']) & (data['-DM'] > 0), 0.0)

    # ATR Calculation using EMA or Wilder's smoothing
    # For ADX, Wilder's smoothing is often used:
    data['ATR'] = data['TR'].ewm(alpha=1/period, adjust=False).mean()
    data['+DI'] = 100 * (data['+DM'].ewm(alpha=1/period, adjust=False).mean() / data['ATR'])
    data['-DI'] = 100 * (data['-DM'].ewm(alpha=1/period, adjust=False).mean() / data['ATR'])

    # DX Calculation
    data['DX'] = (100 * (abs(data['+DI'] - data['-DI']) / (data['+DI'] + data['-DI'])))

    # ADX Calculation (Wilder's smoothing)
    data['ADX'] = data['DX'].ewm(alpha=1/period, adjust=False).mean()

    # Clean up intermediate columns to avoid clutter
    data.drop(['H-L', 'H-Cp', 'L-Cp', '+DM', '-DM', 'DX'], axis=1, inplace=True)

    return data

# Function to calculate On-Balance Volume (OBV)
def calculate_obv(data):
    # OBV is a running total of volume that relates volume to price change.
    # Volume is added on up days and subtracted on down days.
    obv = (data['Volume'].where(data['Close'] > data['Close'].shift(1), 0) +
           data['Volume'].where(data['Close'] < data['Close'].shift(1), 0) * -1).cumsum()
    
    # Fill the first NaN value with the first day's volume
    data['OBV'] = obv.fillna(data['Volume'])
    
    # Calculate a simple moving average of OBV (e.g., 20 period) to identify the OBV trend
    data['OBV_SMA'] = sma(data['OBV'], 20)
    return data

# Function to check for Bullish Engulfing Pattern
def check_bullish_engulfing(data):
    # Ensure there are at least two rows for comparison
    if len(data) < 2:
        return False

    latest = data.iloc[-1]
    previous = data.iloc[-2]

    # Condition 1: Previous candle must be a Bearish (Red) candle
    prev_is_bearish = (previous['Close'] < previous['Open']).bool()
    
    # Condition 2: Latest candle must be a Bullish (Green) candle
    latest_is_bullish = (latest['Close'] > latest['Open']).bool()
    
    # Condition 3: The latest Bullish body must engulf the previous Bearish body
    # (i.e., latest open is below previous close, AND latest close is above previous open)
    engulfing = (latest['Open'] < previous['Close']).bool() and \
                (latest['Close'] > previous['Open']).bool()
    
    # Optional Condition 4: The engulfing should happen after a decline (price should be lower than 4 days ago)
    # This ensures it's a 'reversal' and not just continuation
    is_after_decline = latest['Close'] < data['Close'].iloc[-5:-1].mean()
    
    return prev_is_bearish and latest_is_bullish and engulfing # and is_after_decline

# Old function (rename and keep its content)
def get_daily_data(ticker):
    interval = '1d'  # 1 day interval
    data = yf.download(ticker, period='6mo', interval=interval)
    # Convert index to timezone-aware datetime
    data.index = data.index.tz_localize('Asia/Kolkata')
    return data

# New function to get Weekly data
def get_weekly_data(ticker):
    interval = '1wk'  # 1 week interval
    # Fetch a longer period to ensure enough data for weekly SMAs/EMAs (e.g., 2 years)
    data = yf.download(ticker, period='2y', interval=interval)
    data.index = data.index.tz_localize('Asia/Kolkata')
    return data

# Function to read Nifty stocks from a CSV file and add .NS suffix
def fetch_nifty_stocks(file_path):
    df = pd.read_csv(file_path)
    # Assuming the CSV file has a column named 'Symbol' containing the stock symbols
    nifty_stocks = df['Symbol'].apply(lambda x: x.strip() + '.NS').tolist()
    return nifty_stocks

def main_driver(args):
    """Wrapper function for multiprocessing - takes a tuple of (ticker, percentage)"""
    ticker, percentage = args
    try:
        data = get_daily_data(ticker)  # This is the original daily data
        weekly_data = get_weekly_data(ticker)

        # Calculate MACD
        data = calculate_macd(data)

        # Calculate RSI
        data = calculate_rsi(data)

        # Calculate additional indicators
        data['EMA_44'] = ema(data['Close'], 44)  # 44-period EMA
        data['SMA_10'] = sma(data['Close'], 10)  # 10-period SMA
        data['SMA_20'] = sma(data['Close'], 20)  # 20-period SMA

        # Calculate Bollinger Bands
        data = calculate_bollinger_bands(data, window=20, num_std=2)

        # Calculate ADX
        data = calculate_adx(data, period=14)

        data = calculate_obv(data)

        # Apply SMA to the weekly data's closing price
        weekly_data['SMA_20'] = sma(weekly_data['Close'], 20)

        # Check Price Action Reversal
        is_bullish_engulfing = check_bullish_engulfing(data)

        if is_bullish_engulfing:
            print(f"{ticker}: Bullish Engulfing pattern detected.")

        # Check conditions on the latest rows
        latest_daily_row = data.iloc[-1]
        second_latest_daily_row = data.iloc[-2]
        latest_weekly_row = weekly_data.iloc[-1] # Get the latest weekly row
        # is_bullish = latest_row['+DI'] > latest_row['-DI']

        # Calculate Volume Average for Volume Spike check
        avg_volume_20d = data['Volume'].rolling(window=20).mean().iloc[-1]

        # The stock must be trading above its Weekly SMA_20
        is_weekly_trend_bullish = float(latest_weekly_row['Close']) > float(latest_weekly_row['SMA_20'])

        # Define conditions (example conditions; you can adjust as needed)
        # For instance, you might use ADX > 25 to ensure a strong trend
        # or price close to the lower Bollinger Band for mean reversion opportunities.
        conditions = [
            # (latest_daily_row['RSI'] < 50).bool(),
            # (latest_daily_row['MACD'] > latest_daily_row['Signal_Line']).bool(),
            # (second_latest_daily_row['MACD'] > second_latest_daily_row['Signal_Line']).bool(),
            # (latest_daily_row['MACD'] < 0).bool(),
            # latest_daily_row['ADX'] > 20,
            # (latest_daily_row['Close'] > latest_daily_row['BB_Lower']) & (latest_daily_row['Close'] < latest_daily_row['BB_Middle']),
            (latest_daily_row['SMA_10'] > latest_daily_row['SMA_20']).bool(),

            # is_weekly_trend_bullish,

            # # 7. Volume Spike: Latest volume > 1.5 times 20-day average volume
            # (latest_daily_row['Volume'] > avg_volume_20d * 1.5).bool(),
            
            # # 8. OBV Trend: OBV is above its 20-period Simple Moving Average
            # (latest_daily_row['OBV'] > latest_daily_row['OBV_SMA']).bool()
            # latest_daily_row['+DI'] > latest_daily_row['-DI']  # Checks if the trend is bullish

            is_bullish_engulfing
        ]


        # Calculate number of conditions to meet
        num_conditions = len(conditions)
        num_conditions_to_meet = int(num_conditions * (percentage / 100))

        # # Check if MACD condition is met (as per your original logic)
        # macd_condition_met = conditions[1] and True  
        # if not macd_condition_met:
        #     print(f"MACD conditions not met for {ticker}. Skipping.")
        #     return

        # Count how many conditions are met including MACD
        conditions_met_count = sum(conditions)

        if conditions_met_count >= num_conditions_to_meet:
            data.index = data.index.tz_localize(None)
            
            # Save to Excel if conditions are met
            data.to_excel(f'delete_me\\{ticker}.xlsx', index=True)
            print(f"Conditions met for {ticker}. Data saved to Excel.")
        else:
            print(f"Conditions not met for {ticker}. Skipping.")
    except Exception as e:
        print(f"Failed for {ticker}: {e}")

if __name__ == "__main__":
    # Specify the path to your CSV file with Nifty stocks
    nifty_stocks_file = 'ind_nifty200list.csv'  # or 'ind_nifty500list.csv'
    # nifty_stocks_file = 'testlist.csv'
    nifty_stocks = fetch_nifty_stocks(nifty_stocks_file)
    
    # Specify the percentage of conditions to be met
    percentage = 100  # Adjust as needed

    # Create a list of (ticker, percentage) tuples for multiprocessing
    tasks = [(ticker, percentage) for ticker in nifty_stocks]
    
    # Determine number of processes (use all available CPU cores)
    num_processes = cpu_count()
    print(f"Using {num_processes} processes for parallel execution...")
    
    # Use multiprocessing Pool to process stocks in parallel
    with Pool(processes=num_processes) as pool:
        pool.map(main_driver, tasks)
    
    print("All stocks processed.")
