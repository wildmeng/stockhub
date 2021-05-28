import os
import pandas as pd
import numpy as np
import yfinance as yf

def get_ticker_pd(ticker, period="max", update=False):
    
        stock_pd = yf.Ticker(ticker).history(period=period)
        if len(stock_pd) == 0:
            print('failed to download ', ticker)
            return None
        stock_pd.to_csv(file, index=True)
    else:
        try:
            stock_pd = pd.read_csv(file, sep=',', usecols=['Close'])
            stock_pd['Close'].replace('', np.nan, inplace=True)
            stock_pd.dropna(subset=['Close'], inplace=True)
        except:
            assert False, 'failed to load ' + ticker

        stock_pd = stock_pd.apply(pd.to_numeric, errors='coerce')

    return stock_pd


if __name__ == '__main__':
    print(get_ticker_pd('000002.SZ'))