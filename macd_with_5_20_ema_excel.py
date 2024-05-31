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

# Calculate Pivot Points
data['Pivot'] = (data['High'].shift(1) + data['Low'].shift(1) + data['Close'].shift(1)) / 3
data['R1'] = 2 * data['Pivot'] - data['Low'].shift(1)
data['S1'] = 2 * data['Pivot'] - data['High'].shift(1)
data['R2'] = data['Pivot'] + (data['High'].shift(1) - data['Low'].shift(1))
data['S2'] = data['Pivot'] - (data['High'].shift(1) - data['Low'].shift(1))

# Determine if it's a good time to buy based on MACD, Pivot Points, and EMA conditions
data['Buy_Signal'] = (data['MACD'] > data['Signal']) & (data['Close'] > data['Pivot']) & (data['EMA_5'] > data['EMA_20'])

# Save the DataFrame to Excel
data.to_excel("HDFC_Analysis.xlsx", index=False)

# Plotting
plt.figure(figsize=(14, 14))

# Plot Close Price with 5-day and 20-day EMAs
plt.subplot(5, 1, 1)
plt.plot(data['Date'], data['Close'], label='Close Price')
plt.plot(data['Date'], data['EMA_5'], label='5-day EMA', linestyle='--')
plt.plot(data['Date'], data['EMA_20'], label='20-day EMA', linestyle='--')
plt.title('Stock Price with 5-day and 20-day EMAs')
plt.legend(loc='upper left')
plt.xticks(rotation=45)

# Plot MACD and Signal
plt.subplot(5, 1, 2)
plt.plot(data['Date'], data['MACD'], label='MACD', color='b')
plt.plot(data['Date'], data['Signal'], label='Signal', color='r')
plt.title('MACD and Signal Line')
plt.legend(loc='upper left')
plt.xticks(rotation=45)

# Plot MACD Histogram
plt.subplot(5, 1, 3)
plt.bar(data['Date'], data['MACD_Histogram'], label='MACD Histogram', color='g', alpha=0.3)
plt.title('MACD Histogram')
plt.legend(loc='upper left')
plt.xticks(rotation=45)

# Plot Pivot Points
plt.subplot(5, 1, 4)
plt.plot(data['Date'], data['Pivot'], label='Pivot', color='black', linestyle='--')
plt.plot(data['Date'], data['R1'], label='R1', color='blue', linestyle='--')
plt.plot(data['Date'], data['S1'], label='S1', color='red', linestyle='--')
plt.plot(data['Date'], data['R2'], label='R2', color='blue', linestyle='-.')
plt.plot(data['Date'], data['S2'], label='S2', color='red', linestyle='-.')
plt.title('Pivot Points')
plt.legend(loc='upper left')
plt.xticks(rotation=45)

# Plot Buy Signal
plt.subplot(5, 1, 5)
plt.scatter(data['Date'][data['Buy_Signal']], data['Close'][data['Buy_Signal']], marker='^', color='g', label='Buy Signal')
plt.plot(data['Date'], data['Close'], label='Close Price')
plt.title('Buy Signal')
plt.legend(loc='upper left')
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()
