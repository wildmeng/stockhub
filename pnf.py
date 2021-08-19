import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import gm.api as gm
import glob
import os
from pathlib import Path

gm.set_token('0147eee0d2783671c80d7a618d3fa7a6cc7c9778')

def get_pnf_data(closes, box_size=3, box_precent=True, reverse_cnt=3, round_num=2):
    result = []
    dir = 1
    dates = [closes.index[0]]
    closes = closes.dropna()

    box = box_size
    if box_precent:
        box = round(closes.iloc[-1]*box_size/100.0, round_num)

    if box < 0.01:
        return result, dates, 0

    box_price = closes.iloc[0]
    curr = [0]

    for i, price in enumerate(closes):
        if price is np.nan:
            continue
        change = price - box_price
        if abs(change) < box:
            continue

        if dir*change < 0 and abs(change) < box*reverse_cnt:
            continue

        boxes_cnt = int(abs(change)/box)
        last = curr[-1]
        if dir*change > 0:
            for i in range(boxes_cnt):
                curr.append(last + (i+1)*dir)
        else:
            dates.append(closes.index[i])
            result.append(curr)
            curr = []
            for i in range(boxes_cnt):
                curr.append(last - (i+1)*dir)
            dir = -dir

        box_price += boxes_cnt*box*dir

    if len(curr) > 0:
        result.append(curr)

    return result, dates, box

def get_pause_zone(pnf):
    total = len(pnf)
    common = set(pnf[total-1])
    j = total - 2
    cnt = 1
    while (j > 0):
        result = common.intersection(pnf[j])
        j -= 1
        if len(result) > 0 :
            cnt += 1
            common = result
        else:
            break
    
    return cnt, min(common)

def get_vert_len(pnf, val, start_col):
    last = start_col
    for i in range(start_col - 1, -1, -1):
        if val not in pnf[i]:
            if last -i > 1:
                return last
        else:
            last = i

    return last

def get_pnf_max_min(pnf, start, end):
    pnf_max = -1000
    pnf_min = 1000
    for i in range(start, end+1, -1):
        _min = min(pnf[i])
        if _min < pnf_min:
            pnf_min = _min

        _max = min(pnf[i])
        if _max > pnf_max:
            pnf_max = _max

    return pnf_min, pnf_max

def get_accum_pattern(pnf):
    total = len(pnf)
    vcol = total-1
    v = 0
    for c in pnf[total-1]:
        col = get_vert_len(pnf, c, total-1)
        if col < vcol:
            vcol = col
            v = c

    pnf_min, pnf_max = get_pnf_max_min(pnf, total-1, vcol)
    return vcol, v, pnf_min, pnf_max
   

def plot_pnf(symbol, box_size=3, box_percent=True, reverse=3, return_figure=False, yahool=False):
    if yahool:
        df = yf.Ticker(symbol).history(period='max')
    else:
        df = download_china(symbol, 10000)
        
    if df is None or len(df) == 0:
        print('failed to get history data ')
        return

    closes = df['Close'].round(2)
    data, dates, box = get_pnf_data(closes, box_size, box_percent, reverse)
    
    if box <= 0.01: 
        print('invalid box size')
        return

    x1 = []
    x2 = []
    y1 = []
    y2 = []
    date1 = []
    date2 = []
    for i, v in enumerate(data):
        if i%2 == 0:
            x1 += [i]*len(v)
            y1 += v
            date1 += [str(dates[i].date())]*len(v)
        else:
            x2 += [i]*len(v)
            y2 += v
            date2 += [str(dates[i].date())]*len(v)
        
    trace1 = {
    "mode": "markers", 
    "name": "Up", 
    "type": "scatter", 
    "x": x1, 
    "y": y1, 
    "marker": {
        "size": 5, 
        "color": "rgba(255, 0, 0, 0.9)", 
        #"symbol": "square"
    }, 
    "text": date1,
    }
    trace2 = {
    "mode": "markers", 
    "name": "Down", 
    "type": "scatter", 
    "x": x2, 
    "y": y2, 
    "marker": {
        "size": 5, 
        "color": "rgba(0, 255, 0, 0.9)", 
        #"symbol": 34
    }, 
    "text": date2,
    }

    
    dict_of_fig = dict({
        "data": [trace1, trace2],
        "layout": {"title": {"text": f"{symbol} pnf box:{box} %{box_size} reverse:{reverse}"},
        "yaxis": {"side":"right"},}
    })

    fig = go.Figure(dict_of_fig)
    
    _end = len(data) - 1
    start, val, _min, _max = get_accum_pattern(data)
    if (_end - start > 4):
        fig.add_shape(type="rect",
        x0=start, y0=val, x1=_end, y1=_min,
        fillcolor="LightSkyBlue", opacity=0.5,
        line=dict(
            color="Black",
            width=1,
        ))

    '''
    last = closes[-1]
    target_percent = int(100*(target-last)/last)
    fig.add_hline(y=last, line_dash="dot", line_width=1, line_color='red', annotation_text=f"{last}")
    fig.add_hline(y=target, line_dash="dot", line_width=1, line_color='blue',annotation_text=f"target: {target} {target_percent}%")

    '''
    if return_figure:
        return fig
    else:
        fig.show()

def download_china(symbol, period):
    today = datetime.now()
    
    df = gm.history_n(symbol=symbol, frequency='1d', count=period, fields='close,bob',
            fill_missing='Last', adjust=gm.ADJUST_PREV, end_time=today, df=True)
    df.rename(columns = {'bob':'Date', 'close': 'Close'}, inplace=True)
    df.set_index('Date',inplace=True)
    return df

def scan_market(market, downloader, box_size=3, reverse=3):
    home = str(Path.home())
    list_of_files = glob.glob(f'{home}\\Downloads\\{market}*.csv')
    latest_file = max(list_of_files, key=os.path.getctime)
    print(latest_file)
    stock_df = pd.read_csv(latest_file, dtype={'商品代码':'string'})
    
    #targets = {x: [] for x in box_size}
    #currents = {x: [] for x in box_size}
    accums = []
    currents = []

    for index, row in stock_df.iterrows():
        if row['交易所'] == 'SSE':
            symbol = 'SHSE.' + row['商品代码']
        else:
            symbol = 'SZSE.' + row['商品代码']

        df = downloader(symbol, 10000)
        print(row['商品代码'])
        closes = df['Close'].round(2)
        last = closes.iloc[-1]
        pnf, dates, box = get_pnf_data(closes, box_size, reverse)
        if box < 0.01:
            currents.append(0)
            accums.append(0)
            continue
        start, val, _min, _max = get_accum_pattern(pnf)

        currents.append(int((last-closes.iloc[0])/box) - val)
        accums.append(len(pnf) - start)
    
    stock_df['accums'] = accums
    stock_df['currents'] = currents
    stock_df.to_csv(f'data/{market}-last.csv', index=False)

    #stock_df = stock_df.query('a > 0 and 0 < b < 2')
    print(stock_df.head(10))

if __name__ == '__main__':
    #plot_pnf('SHSE.603026', 3, 3, yahool=False)
    #plot_pnf('SZSE.000027', 0.2, False, 3, yahool=False)
    scan_market('china', download_china, 3, 3)
    #plot_pnf('AAPL', 3, 3)