import pandas as pd
import matplotlib.pyplot as plt

# Load your data
data = pd.read_csv("C:\\data\\vishnu\\trading_with_gpt\\csv\\HDFCBANK.NS.csv")

# Calculate EMAs
data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
data['EMA_20'] = data['Close'].ewm(span=20, adjust=False).mean()
data['EMA_12'] = data['Close'].ewm(span=12, adjust=False).mean()
data['EMA_26'] = data['Close'].ewm(span=26, adjust=False).mean()

# Calculate MACD and Signal line
data['MACD'] = data['EMA_12'] - data['EMA_26']
data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
data['MACD_Histogram'] = data['MACD'] - data['Signal']

# Plotting
plt.figure(figsize=(14, 10))

# Plot Close Price with 5-day and 20-day EMAs
plt.subplot(3, 1, 1)
plt.plot(data['Date'], data['Close'], label='Close Price')
plt.plot(data['Date'], data['EMA_5'], label='5-day EMA', linestyle='--')
plt.plot(data['Date'], data['EMA_20'], label='20-day EMA', linestyle='--')
plt.title('Stock Price with 5-day and 20-day EMAs')
plt.legend(loc='upper left')
plt.xticks(rotation=45)

# Plot MACD and Signal
plt.subplot(3, 1, 2)
plt.plot(data['Date'], data['MACD'], label='MACD', color='b')
plt.plot(data['Date'], data['Signal'], label='Signal', color='r')
plt.title('MACD and Signal Line')
plt.legend(loc='upper left')
plt.xticks(rotation=45)

# Plot MACD Histogram
plt.subplot(3, 1, 3)
plt.bar(data['Date'], data['MACD_Histogram'], label='MACD Histogram', color='g', alpha=0.3)
plt.title('MACD Histogram')
plt.legend(loc='upper left')
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()
