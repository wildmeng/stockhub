
import glob
import os
from pathlib import Path
import gm.api as gm
from datetime import datetime, timedelta
from numpy import append
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import MetaTrader5 as mt5

gm.set_token('0147eee0d2783671c80d7a618d3fa7a6cc7c9778')

ic_path = "C:\\Program Files\\ICMarkets - MetaTrader 5\\terminal64.exe"
xm_path = "C:\\Program Files\\XM MT5\\terminal64.exe"
if not mt5.initialize(path=xm_path):
    print("initialize() failed")
    mt5.shutdown()

def download_yh(exchange, code, period):
    t = datetime.now() - timedelta(days=period+1)
    if exchange == 'HKEX':
        if len(code) < 4:
            code = '0'*(4-len(code)) + code + '.' + 'HK'
        else:
            code = code + '.' + 'HK'
    else:
        if '.' in code:
            code = code.replace('.', '-')  
        elif '/' in code:
            code = code.replace('/', '.')

    try:
        df = yf.Ticker(code).history(start=str(t.date()))
        if len(df) == 0:
            print('failed to download ', code)
            return None
        else:
            print('downloaded ', code)
            df.rename(columns={'Close': 'close'}, inplace=True)
            return df
    except Exception:
        print('failed to download ', code)
        return None

def download_mt5(exchange, code, period):
    try:
        rates = mt5.copy_rates_from_pos(code, mt5.TIMEFRAME_D1, 0, period,)
        if len(rates) == 0:
            print('failed to download ', code)
            return None
        else:
            print('downloaded ', code)
            return pd.DataFrame(rates)
    except Exception:
        print('failed to download ', code)
        return None

def download_china(exchange, code, period):
    today = datetime.now()

    if exchange == 'SSE':
        exchange = 'SHSE'
    symbol = exchange + '.' + code
    return gm.history_n(symbol=symbol, frequency='1d', count=period, fields='close',
            fill_missing='Last', adjust=gm.ADJUST_PREV, end_time=today, df=True)


def find_start_rsi(rsi):
    first_i = 0
    min_rsi = 0
    for i in range(1, len(rsi)):
        if rsi[-i] < 40:
            print('first weak rsi ', rsi[-i])
            first_i = i
            min_rsi = i
            break
        
    if first_i == 0:
        print('failed to find starting rsi!')
        return None

    for i in range(first_i+1, len(rsi)):
        if rsi[-i] < rsi[-min_rsi]:
            min_rsi = i
        elif rsi[-i] > 50:
            break

    return min_rsi
    
def do_rsi(market, downloader):
    home = str(Path.home())
    list_of_files = glob.glob(f'{home}\\Downloads\\{market}*.csv')
    latest_file = max(list_of_files, key=os.path.getctime)
    print(latest_file)
    df = pd.read_csv(latest_file, dtype={'商品代码':'string'})

    period = 14
    strong_rsi = 70
    
    found = []
    for index, row in df.iterrows():
        data = downloader(row['交易所'], row['商品代码'], 500)
        if data is None or len(data) < 200:
            continue

        rsi = ta.rsi(data["close"], length=period)
        if rsi[-1] < strong_rsi:
            continue

        rsi_start = find_start_rsi(rsi)
        last = rsi[-rsi_start:]
        min_idx = last.close.idxmin()
        max_idx = last.close.idxmax()
        min_i = last.index.get_loc(min_idx)
        max_i = last.index.get_loc(max_idx)

        min_close = last.loc[min_idx, 'close']
        max_close = last.loc[max_idx, 'close']

        
do_rsi('china', download_mt5)
#do('future', download_china)
#do('hongkong', download_yh)
#do('china', download_china)
#do('america', download_yh)