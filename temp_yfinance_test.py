import yfinance as yf
data = yf.download('GARAN.IS', period='5d', interval='1d')
print(data.empty)