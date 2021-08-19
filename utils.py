import glob
import os
from pathlib import Path
import pandas as pd

def read_latest_csv(prefix='china'):
    home = str(Path.home())
    list_of_files = glob.glob(f'{home}\\Downloads\\{prefix}*.csv')
    latest = max(list_of_files, key=os.path.getctime)
    df = pd.read_csv(latest, dtype={'商品代码':'string'})
    return df

def get_yh_symbol(row):
    if row['交易所'] == 'SSE':
        return row['商品代码'] + '.SS'
    else:
        return row['商品代码'] + '.SZ'

def get_yh_symbols(df):
    symbols = df.apply(get_yh_symbol, axis=1)
    return list(symbols)