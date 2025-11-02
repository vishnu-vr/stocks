import pandas as pd
import yfinance as yf
import warnings
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
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
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
    data['EMA_44'] = ema(data['Close'], 44)  # 44-period EMA
    data['SMA_10'] = sma(data['Close'], 10)  # 10-period SMA
    data['SMA_20'] = sma(data['Close'], 20)  # 20-period SMA

    # Calculate Bollinger Bands
    data = calculate_bollinger_bands(data, window=20, num_std=2)

    # Calculate ADX
    data = calculate_adx(data, period=14)

    # Check conditions on the latest row
    latest_row = data.iloc[-1]
    second_latest_row = data.iloc[-2]
    is_bullish = latest_row['+DI'] > latest_row['-DI']

    # Define conditions (example conditions; you can adjust as needed)
    # For instance, you might use ADX > 25 to ensure a strong trend
    # or price close to the lower Bollinger Band for mean reversion opportunities.
    conditions = [
        (latest_row['RSI'] < 50).bool(),
        (latest_row['MACD'] > latest_row['Signal_Line']).bool(),
        (second_latest_row['MACD'] > second_latest_row['Signal_Line']).bool(),
        (latest_row['MACD'] < 0).bool(),
        # latest_row['ADX'] > 20,
        # (latest_row['Close'] > latest_row['BB_Lower']) & (latest_row['Close'] < latest_row['BB_Middle']),
        (latest_row['SMA_10'] > latest_row['SMA_20']).bool(),
        # latest_row['+DI'] > latest_row['-DI']  # Checks if the trend is bullish
    ]


    # Calculate number of conditions to meet
    num_conditions = len(conditions)
    num_conditions_to_meet = int(num_conditions * (percentage / 100))

    # Check if MACD condition is met (as per your original logic)
    macd_condition_met = conditions[1] and True  
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
    # Specify the path to your CSV file with Nifty stocks
    # nifty_stocks_file = 'ind_nifty200list.csv'  # or 'ind_nifty500list.csv'
    nifty_stocks_file = 'testlist.csv'
    nifty_stocks = fetch_nifty_stocks(nifty_stocks_file)
    
    # Specify the percentage of conditions to be met
    percentage = 100  # Adjust as needed

    for ticker in nifty_stocks:
        print(f"Processing {ticker}...")
        try:
            main_driver(ticker, percentage)
        except Exception as e:
            print(f"Failed for {ticker}: {e}")
