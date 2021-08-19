
import pnf
import glob

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


list_of_files = glob.glob(f'data/*-last.csv')
print(list_of_files)
markets = [x.rsplit('-', 1)[0].split('\\')[1] for x in list_of_files]
print('markets:', markets)
markets_df = {}
for i, v in enumerate(list_of_files):
    df = pd.read_csv(v, dtype={'商品代码':'string'})
    df = df[df['target'] > 30]
    markets_df[markets[i]] = df

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

controls = dbc.Card(
    [
        dbc.FormGroup(
            [
                dbc.Label("Country"),
                dcc.Dropdown(
                    id="country",
                    options=[
                        {'label': i, 'value': i} for i in ['china', 'america']],
                    value="china",
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("BoxSize"),
                dcc.Input(
                    id="BoxSize",
                    type='number', min=1, max=20,
                    value="3",
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Reverse"),
                dcc.Input(
                    id="Reverse",
                    type='number', min=1, max=5,
                    value="3",
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("MinTarget"),
                dcc.Input(
                    id="MinTarget",
                    type='number', min=1, max=5,
                    value="30",
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
                dbc.Col(html.Div(id='stock-table'), md=2),
                dbc.Col(dcc.Graph(id="pnf-graph"), md=8),
            ],
            align="top",
        ),
    ],
    fluid=True,
)

current_table_df = None

@app.callback(
    Output('stock-table', 'children'),
    Input('country', 'value'),
    Input('MinTarget', 'value'),)
def select_country(country, min_target):
    global current_table_df
    df = markets_df[country]
    df = df[df['target'] > int(min_target)]
    df = df[["说明", "商品代码", "target"]]
    current_table_df = df

    return [
        dash_table.DataTable(
        id='stock_table',
        #filter_action="native",
        #row_selectable='single',
        #page_size=30,
        #style_as_list_view=True,
        fixed_rows={'headers': True},
        #style_table={'overflowY': 'auto', 'overflowX': 'auto', 'display': 'inline-block'},
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        style_cell={'textAlign': 'center'})]

@app.callback(
    Output('pnf-graph', 'figure'),
    Input('BoxSize', 'value'),
    Input('Reverse', 'value'),
    Input('stock_table', 'selected_cells'))
def update_figure(box, reverse, row):
    if row == None:
        return {}
    info = current_table_df.iloc[row[0]['row']]
    code = info['商品代码']
    if code.startswith('6'):
        symbol = 'SHSE.' + code
    else:
        symbol = 'SZSE.' + code
    print(symbol)
    fig = pnf.plot_pnf(symbol, int(box), int(reverse), return_figure=True)
    fig.update_layout(dragmode='pan')
    # fig.update_yaxes(fixedrange=True)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=80)
