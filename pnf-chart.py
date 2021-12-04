import plotly.express as px
from itertools import cycle
import pandas as pd
import yfinance as yf
import utils

from datetime import datetime
from enum import unique
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash_html_components.S import S
from dash_html_components.Script import Script
import dash_table
import numpy as np
import dash_bootstrap_components as dbc
import pnf


df = pd.read_csv('data/china-last.csv', dtype={'商品代码':'string'})

df.sort_values(by=['accums'], inplace=True, ascending=False)
df_data = df
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

controls = dbc.Card(
    [
        dbc.FormGroup(
            [
                dbc.Label("MinAccum"),
                dcc.Input(
                    id="MinAccum",
                    type='number', min=3, max=20,
                    value="5",
                )
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("MaxPosition"),
                dcc.Input(
                    id="MaxPosition",
                    type='number', min=-10, max=100,
                    value="10",
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("MinPosition"),
                dcc.Input(
                    id="MinPosition",
                    type='number', min=-10, max=100,
                    value="-10",
                ),
            ]
        ),
    ],
    body=True,
)

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(controls, md=2),
                dbc.Col(dcc.Graph(id="symbols-graph"), md=4),
                dbc.Col(dcc.Graph(id="stocks-graph"), md=5),

            ],
            align="top",
            no_gutters = True
        ),
        html.Div(id='tradingview_ca4da', style={'width': '90%', 'height':'450px', 'marginLeft': '5%', "marginRight": "5%"}),
        html.Div(id='null', style={'height':'100px'})
    ],
    fluid=True,
)

app.clientside_callback(
    """
    function(selectData) {
        if (!selectData || selectData.points.length === 0) {
            return ''
        }
        console.log('data', selectData);

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
    Input('symbols-graph', 'selectedData')
)

@app.callback(
    Output('symbols-graph', 'figure'),
    Input('MinAccum', 'value'))
def update_figure(minAccum):
    df_data = df.loc[df['accums'] >= int(minAccum)]
    fig = px.scatter(df_data, x="currents", y="accums",
        hover_name="说明", custom_data=["交易所", "商品代码"])

    fig.update_layout(clickmode='event+select', dragmode='pan')
    return fig


@app.callback(
    Output('stocks-graph', 'figure'),
    Input('symbols-graph', 'clickData'),)
def select_industry(data):
    if data is None:
        return {}
    print(data)

    market = data['points'][0]['customdata'][0]
    symbol = data['points'][0]['customdata'][1]
    if market == 'SSE':
        market = 'SHSE'

    symbol = market + '.' + symbol
    return pnf.plot_pnf(symbol, return_figure=True)

if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=9090)
