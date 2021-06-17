import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

def get_pnf_data(df, box_percent=3, reverse_cnt=3, round_num=2):
    result = []
    dir = 1
    dates = [df.index[0]]
    closes = df['Close']
    closes = closes.round(round_num)

    box_price = closes[0]
    box = round(closes[-1]*box_percent/100.0, round_num)
    curr = [box_price]

    for i, price in enumerate(df['Close']):
        change = price - box_price
        if abs(change) < box:
            continue

        if dir*change < 0 and abs(change) < box*reverse_cnt:
            continue

        boxes_cnt = int(abs(change)/box)
        if dir*change > 0:
            for i in range(boxes_cnt):
                curr.append(box_price + (i+1)*box*dir)
        else:
            dates.append(df.index[i])
            result.append(curr)
            curr = []
            for i in range(boxes_cnt):
                curr.append(box_price - (i+1)*box*dir)
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

def plot_pnf(symbol, box_percents=3, reverse=3, return_figure=False):
    df = yf.Ticker(symbol).history(period='max')
    if df is None or len(df) == 0:
        print('failed to get history data')
        return

    data, dates, box = get_pnf_data(df, box_percents, reverse)
    
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

    last = df['Close'][-1]
    dict_of_fig = dict({
        "data": [trace1, trace2],
        "layout": {"title": {"text": f"{symbol} pnf box:{box} %{box_percents} reverse:{reverse}"},
        "yaxis": {"side":"right"},}
    })

    fig = go.Figure(dict_of_fig)
    
    cnt, price = get_pause_zone(data)
    fig.add_shape(type="rect",
    x0=len(data)-cnt, y0=price, x1=len(data)-1, y1=price + box*reverse*cnt,
    fillcolor="LightSkyBlue", opacity=0.5,
    line=dict(
        color="Black",
        width=1,
    ),)


    fig.add_hline(y=last, line_dash="dot", line_width=1, line_color='red')
    
    if return_figure:
        return fig
    else:
        fig.show()

if __name__ == '__main__':
    plot_pnf('600508.SS', 3, 3)
    #plot_pnf('AAPL', 3, 3)