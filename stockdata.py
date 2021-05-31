
import glob
import os
from pathlib import Path
import gm.api as gm
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import MetaTrader5 as mt5

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
    return gm.history_n(symbol=symbol, frequency='1d', count=period*3, fields='close',
            fill_missing='Last', adjust=gm.ADJUST_PREV, end_time=today, df=True)

def do(market, downloader):
    home = str(Path.home())
    list_of_files = glob.glob(f'{home}\\Downloads\\{market}*.csv')
    latest_file = max(list_of_files, key=os.path.getctime)
    print(latest_file)
    df = pd.read_csv(latest_file, dtype={'商品代码':'string'})
    period = 250
    above_ma1_percents = []
    above_ma2_percents = []
    max_change = []
    for index, row in df.iterrows():
        data = downloader(row['交易所'], row['商品代码'], period)
        if data is None or len(data) < period*3-1:
            above_ma1_percents.append(-1)
            above_ma2_percents.append(-1)
            max_change.append(-1)
            continue

        _max = data['close'].iloc[-period:].max()
        _min = data['close'].iloc[-period:].min()
        change = int((_max - _min)*100/_min)
        if change < 0:
            above_ma1_percents.append(-1)
            above_ma2_percents.append(-1)
            max_change.append(-1)
            continue

        ma = data['close'].rolling(window=period).mean()
        if ma.iloc[-1] <= ma.iloc[-2]:
            above_ma1_percents.append(-1)
            above_ma2_percents.append(-2)
            max_change.append(-1)
            continue

        max_change.append(change)

        ma_diff = data['close'] - ma
        ma_diff1 = ma_diff[-period:]
        diff1 = ma_diff1[ma_diff1 > 0]

        above_ma1_percents.append(int(100*len(diff1)/period))

        ma_diff2 = ma_diff[-2*period:-period]
        diff2 = ma_diff2[ma_diff2 > 0]
        above_ma2_percents.append(int(100*len(diff2)/period))

    df['aboveMa1'] = above_ma1_percents
    df['aboveMa2'] = above_ma2_percents
    df['maxChange'] = max_change
    df.to_csv(f'data/{market}-last.csv', index=False)
    print(df.head(10))

do('xm-cfd', download_mt5)
#do('future', download_china)
#do('hongkong', download_yh)
#do('china', download_china)
#do('america', download_yh)