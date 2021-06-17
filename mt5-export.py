from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5
from pathlib import Path

# connect to MetaTrader 5
ic_path = "C:\\Program Files\\ICMarkets - MetaTrader 5\\terminal64.exe"
xm_path = "C:\\Program Files\\XM MT5\\terminal64.exe"
if not mt5.initialize(path=xm_path):
    print("initialize() failed")
    mt5.shutdown()

# request connection status and parameters
# print(mt5.terminal_info())
# get data on MetaTrader 5 version
# print(mt5.account_info())

def export_csv():
    symbols = mt5.symbols_get()
    home = str(Path.home())
    df = pd.DataFrame()

    df['商品代码'] = [x.name for x in symbols]
    df['交易所'] = [x.exchange for x in symbols]
    df['说明'] = [x.description for x in symbols]
    df.to_csv(f'{home}\\Downloads\\xm-cfd.csv',index=False)

def get_all_data():
    symbols = mt5.symbols_get()
    print(len(symbols))
    for i, v in enumerate(symbols):
        rates = mt5.copy_rates_from_pos(v.name, mt5.TIMEFRAME_D1, 0, 1000,)
        if rates is None:
            print('failed to download', v.name)
            continue
        print(i, 'downloaded ', v.name, v.description, len(rates))

def get_data(symbol):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 1000,)
    df = pd.DataFrame(rates)
    print(df)

get_all_data()

mt5.shutdown()
