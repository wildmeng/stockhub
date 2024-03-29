import glob
import os
from pathlib import Path
import pandas as pd
import math

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

def _splitSymbol(symbol):
    sep = '.'
    if ':' in symbol:
        sep = ':'

    if sep not in symbol:
        return symbol

    code = symbol.split(sep)[1]
    market = symbol.split(sep)[0]
    return market, code

class MyStocks:
    def __init__(self):
        self.df = pd.read_csv('data/my-list.csv', 
        dtype={'商品代码':'string', 'stop':'string',
         'target':'string','open':'string','close':'string'}, delimiter=',', index_col=False)

    def getAllSymbols(self):
        res = self.df.apply(lambda row: self._makeSymbol(row), axis=1)
        # print(res)
        if len(res) == 0:
            return []
        else:
            return res.to_list()

    def get(self, sym, item):
        market, code = _splitSymbol(sym)
        return self.df.loc[(self.df['商品代码'] == code), item].values[0]

    def update(self, symbol, item, value):
        market, code = _splitSymbol(symbol)
        code_list = self.df['商品代码']
        if code in code_list.values:
            self.df.loc[(self.df['商品代码'] == code), item] = value
        else:
            if market == 'SHSE':
                market = 'SSE'
            row = {"交易所":market, "商品代码":code, item:value, }
            self.df = self.df.append(row, ignore_index=True, ) 

    def addStock(self, symbol):
        market, code = _splitSymbol(symbol)
        code_list = self.df['商品代码']
        if code in code_list.values:
            print('already in the list')
            return

        if market == 'SHSE':
            market = 'SSE'

        row = {"交易所":market, "商品代码":code}
        self.df = self.df.append(row, ignore_index=True, )

    def delStock(self, symbol):
        market, code = _splitSymbol(symbol)
        code_list = self.df['商品代码']
        if code not in code_list.values:
            print('not in the list')
            return

        self.df = self.df[self.df['商品代码'] != code]

    def flush(self):
        #self.df.fillna(0, inplace=True)
        #print(self.df)
        self.df.to_csv('data/my-list.csv', index=False)


    def _makeSymbol(self, row):
        market = row['交易所']
        if market == 'SSE':
            market = 'SHSE'

        return market + '.' + row['商品代码']

    def getOrder(self, name):
        result = []
        for index, row in self.df.iterrows():
            order = (row[name])
            if pd.isnull(order) or order.strip() == '' or order.startswith('#'):
                continue

            result.append([self._makeSymbol(row), order])

        return result

if __name__ == "__main__":
    stocks = MyStocks()
    print(stocks.getOrder('open'))
