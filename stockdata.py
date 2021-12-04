
import glob
import os
from pathlib import Path
import gm.api as gm
from datetime import datetime, timedelta
from numpy import average
import pandas as pd
import yfinance as yf
import MetaTrader5 as mt5
import pnf

gm.set_token('0147eee0d2783671c80d7a618d3fa7a6cc7c9778')

ic_path = "C:\\Program Files\\ICMarkets - MetaTrader 5\\terminal64.exe"
xm_path = "C:\\Program Files\\XM MT5\\terminal64.exe"
if not mt5.initialize(path=xm_path):
    print("initialize() failed")
    mt5.shutdown()

def download_yh(exchange, code, period):
    t = datetime.now() - timedelta(days=3*365)
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
        rates = mt5.copy_rates_from_pos(code, mt5.TIMEFRAME_D1, 0, 800,)
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
    return gm.history_n(symbol=symbol, frequency='1d', count=period, fields='close,low',
            fill_missing='Last', adjust=gm.ADJUST_PREV, end_time=today, df=True)

def filter_1(row, downloader):
    data = downloader(row['交易所'], row['商品代码'], 3000)
    if data is None or 'close' not in data:
        return pd.Series([0], index=['PauseDays'])

    close = data['close']
    if len(close) < 500:
        return False

    # arguments
    average = 100
    range_percents = 20
    max_outof_range = 200
    min_range_len = 500

    print(row['商品代码'])
    mean = close[-average:].mean()
    upper = mean*(1.0 + range_percents/200.0)
    lower = mean*(1.0 - range_percents/200.0)

    #print(close[::-1])
    outof_range = 0
    index = 0
    outof_range_start = 0
    for price in close[::-1]:
        index += 1
        if price > upper or price < lower:
            if outof_range == 0:
                outof_range_start = index
            outof_range += 1
        else:
            outof_range = 0
        if outof_range > max_outof_range:
            break

    return pd.Series([outof_range_start], index=['PauseDays'])

def filter_2(row, downloader):
    data = downloader(row['交易所'], row['商品代码'], 3000)
    if data is None or 'close' not in data:
        return pd.Series([0], index=['PauseDays'])

def do_search(market, downloader, filter):
    home = str(Path.home())
    list_of_files = glob.glob(f'{home}\\Downloads\\{market}*.csv')
    latest_file = max(list_of_files, key=os.path.getctime)
    print(latest_file)
    df = pd.read_csv(latest_file, dtype={'商品代码':'string'})
    print('total', len(df))
    #df = df[df['RSI(14)'] > 40]
    df_res = df.apply(filter, axis=1, args=(downloader,), )
    df_res = pd.concat([df, df_res], axis=1, join='inner')
    df_res = df_res[df_res['PauseDays'] > 500]
    print('total', len(df_res))
    df_res.to_csv(f'data/{market}-result.csv', index=True)

#do_ma250('xm-cfd', download_mt5)
#do('future', download_china)
#do('hongkong', download_yh)
do_search('china', download_china, filter_1)
#do('america', download_yh)