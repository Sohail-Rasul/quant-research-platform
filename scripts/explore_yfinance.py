#Importing Modules
import yfinance as yf

#Downloading Data
ticker = yf.Ticker("RELIANCE.NS")

#Historical Market Data
data = ticker.history(period="1mo",  auto_adjust = False) # This is the dataframe

#Information about the ticker
info = ticker.info
print(info.keys())

#Information about the dataframe
print("Shape: ")
print(data.shape)

print("Columns: ")
print(data.columns)

print("Data Types: ")
print(data.dtypes)

print("Index: ")
print(data.index)

print("Null Check: ")
print(data.isnull().sum())

print("Head & Tail: ")
print(data.head())
print(data.tail())
