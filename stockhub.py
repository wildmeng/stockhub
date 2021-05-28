
from datetime import datetime
from enum import unique
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash_html_components.S import S
from dash_html_components.Script import Script
from numpy import tile
import plotly.express as px
import plotly.graph_objects as go
import json
import pandas as pd
import gm.api as gm
import glob
import yfinance as yf

gm.set_token('0147eee0d2783671c80d7a618d3fa7a6cc7c9778')

list_of_files = glob.glob(f'data/*-last.csv')
markets = [x.split('-')[0].split('\\')[1] for x in list_of_files]
markets_df = {}

tv_style = {'width': '90%', 'height':'500px', "marginLeft": "5%", "marginRight": "5%"}

for i, v in enumerate(list_of_files):
    df = pd.read_csv(v, dtype={'商品代码':'string'})
    df = df[df['aboveMa1'] > 60]
    df = df[df['aboveMa2'] < 70]
    df = df[df['maxChange'] < 100]
    markets_df[markets[i]] = df

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div([
    dcc.Tabs(id='market', value='china',
        children=[dcc.Tab(label=x, value=x) for x in markets]),
    dcc.Graph(
        id='symbols-graph', style=tv_style,
            config={'scrollZoom':True}
    ),
    html.Div(id='tradingview_ca4da', style={'width': '90%', 'height':'450px', 'marginLeft': '5%', "marginRight": "5%"}),
    dcc.Graph(
        id='stock-graph', style=tv_style, config={'scrollZoom':True}
    ),
    html.Div(id='null', style={'height':'100px'}),
    ])

app.clientside_callback(
    """
    function(selectData, market) {
        if (market === 'hongkong' || market === 'future' || !selectData || selectData.points.length === 0) {
            return ''
        }

        var symbols = selectData.points.map(p => p.customdata[0] + ':' + p.customdata[1])
        console.log(symbols);
        function create_tv() {
            new TradingView.widget(
            {
            "autosize": true,
            "symbol": symbols[0],
            "timezone": "Asia/Shanghai",
            "interval": "D",
            "theme": "light",
            "style": "1",
            "locale": "zh_CN",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "range": "12M",
            "details": true,
            "allow_symbol_change": true,
            "hide_side_toolbar": false,
            "studies": [
            "MASimple@tv-basicstudies"
            ],
            "watchlist": symbols,
            "container_id": "tradingview_ca4da"
        });
    }

    if (typeof TradingView === 'undefined') {
        var script = document.createElement('script');
        script.onload = create_tv
        script.src = "https://s3.tradingview.com/tv.js";
        document.head.appendChild(script);
    } else {
        create_tv()
    }

    return ''
    }
    """,
    Output(component_id='null', component_property='children'),
    Input('symbols-graph', 'selectedData'),
    Input('market', 'value')
)

@app.callback(
    Output('symbols-graph', 'figure'),
    Input('market', 'value'))
def update_figure(market):
    if market not in markets_df:
        print('invalid market:', market)
        return {}
    fig = px.scatter(markets_df[market], x="aboveMa1", y="aboveMa2",
        hover_name="说明", custom_data=["交易所", "商品代码"])

    fig.update_layout(clickmode='event+select', dragmode='pan')
    return fig

@app.callback(
    Output('stock-graph', 'figure'),
    Input('symbols-graph', 'clickData'),
    Input('market', 'value'))
def update_figure(data, market):
    print('update_figure', market)
    if data is None:
        return {}
    if market != 'hongkong' and market != 'future':
        return {}

    if market == 'hongkong':
        symbol = data['points'][0]['customdata'][1]
        symbol = '0'*(4-len(symbol)) + symbol + '.' + 'HK'
        df = yf.Ticker(symbol).history(period='5y')
    else:
        symbol = data['points'][0]['customdata'][0] + '.' + data['points'][0]['customdata'][1]
        df = gm.history_n(symbol=symbol, frequency='1d', count=1000, fields='open,close,high,low',
            fill_missing='Last', adjust=gm.ADJUST_PREV, end_time=datetime.now(), df=True)
        df.rename(columns={'close': 'Close', 'high':'High', 'low':'Low', 'open':'Open'}, inplace=True)
        print('update_figure', df)
    # print(df)
    df['MA250'] = df.Close.rolling(250).mean()

    fig = go.Figure(data=[go.Candlestick(x=df.index,
                                     open=df.Open,
                                     high=df.High,
                                     low=df.Low,
                                     close=df.Close),
                      go.Scatter(x=df.index, y=df.MA250, line=dict(color='orange', width=1))])
    fig.update_layout(xaxis_rangeslider_visible=False, title=data['points'][0]['hovertext'] + ' ' + symbol,
        dragmode='pan')
    fig.update_yaxes(fixedrange=True)
    return fig

@app.callback(
    Output('tradingview_ca4da', 'style'),
    Output('stock-graph', 'style'),
    Input('market', 'value'))
def hide_graph(market):
    if market == 'hongkong' or market == 'future':
        return {'display':'none'}, tv_style
    else:
        return tv_style, {'display':'none'}


if __name__ == '__main__':
    app.run_server(debug=True, port=80, host='0.0.0.0')
