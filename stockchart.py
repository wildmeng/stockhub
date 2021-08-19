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

#df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')
df = utils.read_latest_csv()
df_industry = df[['行业']]
df_industry.drop_duplicates(subset=['行业'], inplace=True)
#df_industry = df_industry.groupby('行业', as_index=False).median()
#df_industry = df_industry.round(0)
#df_industry.sort_values(by=['RSI(14)'], inplace=True, ascending=False)
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
                dbc.Label("Period"),
                dcc.Dropdown(
                    id="period",
                    options=[
                        {'label': i, 'value': i} for i in ['1mo', '3mo', '6mo', '1y', '2y', '5y', 'max']],
                    value="6mo",
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Top Stocks"),
                dcc.Input(
                    id="stocks_top",
                    type='number', min=1, max=100,
                    value="10",
                ),
            ]
        ),
    ],
    body=True,
)

table = html.Div([
    dash_table.DataTable(
    id='industry_table',
    #filter_action="native",
    #row_selectable='single',
    #page_size=30,
    #style_as_list_view=True,
    fixed_rows={'headers': True},
    #style_table={'overflowY': 'auto', 'overflowX': 'auto', 'display': 'inline-block'},
    columns=[{"name": i, "id": i} for i in df_industry.columns],
    data=df_industry.to_dict('records'),
    style_cell={'textAlign': 'center'}
)])

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(controls, md=2),
                dbc.Col(table, md=2),
                dbc.Col(dcc.Graph(id="stocks-graph"), md=8),
            ],
            align="top",
        ),
    ],
    fluid=True,
)


@app.callback(
    Output('stocks-graph', 'figure'),
    Input('industry_table', 'selected_cells'),
    Input('period', 'value'),
    Input('stocks_top', 'value'))  
def select_industry(rows, period, top):
    if rows is None:
        return {}
    industry = df_industry['行业'].iloc[rows[0]['row']]
    print(industry, period, top)
   
    data = df[df['行业'] == industry].sort_values('RSI(14)', ascending=False).head(int(top))
    symbols = utils.get_yh_symbols(data)
    symbols.append('000001.SS')
    all_df = []
    print('total:', len(symbols))
    for sym in symbols:
        print('download', sym)
        d = yf.Ticker(sym).history(period=period)
        d.rename(columns={'Close': sym}, inplace=True)
        #d = d.rolling(window=30).apply(lambda x: round((x[-1]-x[0])/x[0], 1))
        d = d[sym]
        d = d/d[0] - 1.0
        all_df.append(d)

    print('downloaded')
    stocks_df = pd.merge(all_df[0], all_df[1], on="Date", how='outer')
    for x in all_df[2:]:
        stocks_df = pd.merge(stocks_df, x, on="Date", how='outer')

    print('merged')
    print(stocks_df)
    title = f'{industry} {period}'
    fig = px.line(stocks_df, x=stocks_df.index, y=stocks_df.columns, title=title)
    fig.layout.yaxis.tickformat = ',.0%'
    #fig['layout']['yaxis']['autorange'] = "reversed"
    fig.layout.update()
    print('finished')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=80)
