
from datetime import datetime
from enum import unique
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash_html_components.S import S
from dash_html_components.Script import Script
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import gm.api as gm
import pnf
import yfinance as yf
import MetaTrader5 as mt5

gm.set_token('0147eee0d2783671c80d7a618d3fa7a6cc7c9778')
ic_path = "C:\\Program Files\\ICMarkets - MetaTrader 5\\terminal64.exe"
xm_path = "C:\\Program Files\\XM MT5\\terminal64.exe"
if not mt5.initialize(path=xm_path):
    print("initialize() failed")

tv_style = {'width': '90%', 'height':'500px', "marginLeft": "5%", "marginRight": "5%"}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div([
    dcc.Input(id='symbol', value='000001.SS', type='text'),
    dcc.Checklist(
        id='charts',
        options=[
            {'label': 'TradingView', 'value': 'TV'},
        ],
        value=['TV']
    ),
    dcc.Graph(
        id='pnf-graph', style=tv_style, config={'scrollZoom':True}
    ),
    html.Div(id='tradingview-graph', style={'width': '90%', 'height':'450px', 'marginLeft': '5%', "marginRight": "5%"}),
    
    html.Div(id='null', style={'height':'100px'}),
    ])

app.clientside_callback(
    """
    function(charts) {
        if (charts.length <= 0) {
            return ''
        }

        function create_tv() {
            new TradingView.widget(
            {
            "autosize": true,
            "symbol": "SSE:000001",
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
            //"watchlist": symbols,
            "container_id": "tradingview-graph"
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
    Input('charts', 'value')
)

@app.callback(
    Output('tradingview-graph', 'style'),
    Input('charts', 'value'))
def hide_graph(charts):
    if len(charts) > 0:
        return tv_style
    else:
        return {'display':'none'}

@app.callback(
    Output('pnf-graph', 'figure'),
    Input('symbol', 'value'))
def update_figure(symbol):
    fig = pnf.plot_pnf(symbol, return_figure=True)
    fig.update_layout(dragmode='pan')
    return fig
    
if __name__ == '__main__':
    app.run_server(debug=True, port=80, host='127.0.0.1')
