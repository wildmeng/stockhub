
# encoding:utf-8

from turtle import position
from xmlrpc.client import FastParser
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, ALL
import dash_bootstrap_components as dbc
from dash import callback_context
import utils
import numpy as np
import pandas as pd
import json
import math


n_col = 3
n_row = 10
stocks = []
stocks_page = []
tabs_name = '行业'
fav_df = pd.read_csv('data/favorite.csv', dtype={'code':'string'}, delimiter=',', index_col=False)
df = utils.read_latest_csv()
industries = df['行业'].unique()
industries = np.append(industries, ['加密货币', '期货', '持有', '自选'])

f = open('data/stockhub.json','r', encoding='utf-8')
page_state = json.load(f)
f.close()
sortbyDropdown = dcc.Dropdown(
    id='SortBy',
    options=[
        {'label': '市场价值', 'value': '市场价值'},
        {'label': '单周表现', 'value': '单周表现'},
        {'label': '3个月表现', 'value': '3个月表现'},
        {'label': '6个月表现', 'value': '6个月表现'},
        {'label': '年表现', 'value': '年表现'}
    ],
    value='市场价值',
    style={'width': '100px'}
    )

options = dcc.Checklist(
    id='opts',
    options=[
        {'label': '降序', 'value': 'decending'},
    ],
    value=['decedent'],
    labelStyle={'display': 'inline-block'},
    style={'display': 'inline-block', 'flex': 1,
           'padding': 10}
)

opts = html.Div([
    sortbyDropdown,
    options,
], id="header", style={'display': 'flex', 'flex-direction': 'right'})

app = dash.Dash(external_stylesheets=[
                dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

tv_style = {'width': '96%', 'height': '350px',
            'marginLeft': '0%', "marginRight": "2%", 'position': 'obsolute'}

tabs = html.Div(id='tabs-div')
pages = html.Div(id='pages-div')

def save_json():
    with open("data/stockhub.json", "w", encoding='utf-8') as f:
        json.dump(page_state, f, indent = 4, ensure_ascii=False)

def cell(row, col):
    id = (row-1)*n_col + (col-1)
    button_type = 'Add'
   
    if stocks_page[id] in fav_df['code'].values:
        button_type = 'Del'
    button = html.Button(button_type, id={'type':button_type, 'index':id}, style={'position':'absolute', 'left':'0', 'top':'0', 'z-index': '0'})
    return html.Div(children=[html.Div(id=f"tv{id}", style=tv_style), button], style={'position': 'relative'})

def creat_row(stocks, row, total_rows):
    if row < total_rows:
        return [dbc.Col(cell(row, col)) for col in range(1, n_col+1)]
    else:
        last_row_cnt = len(stocks) - (total_rows-1)*n_col
        return [dbc.Col(cell(row, col)) for col in range(1, last_row_cnt+1)]

def create_tv(stocks) :
    rows = (len(stocks)+2)//n_col
    return [dbc.Row(creat_row(stocks, row, rows), align="top",) for row in range(1, rows+1)]

div_tv = html.Div(id='div-tv', children='')

app.layout = dbc.Container([opts, tabs, pages] + [div_tv] + [html.Div(id='null', style={'height': '10px'}),
                                                  html.Div(id='symbols', style={
                                                      'display': 'none'}),
                                                  html.Div(id='handlers', style={'display': 'none'})], fluid=True,
                           )

app.clientside_callback(
    """
    function(symbols) {
        console.log('symbols', symbols);
        const syms = symbols.split(',');

        function create_tv(div, symbol='SSE:000001') {
            new TradingView.widget(
            {
            "autosize": true,
            "width":400,
            "heigth":400,
            "symbol": symbol,
            "timezone": "Asia/Shanghai",
            "interval": "D",
            "theme": "light",
            "style": "1",
            "locale": "zh_CN",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            //"range": "60M",
            "details": false,
            "allow_symbol_change": false,
            "hide_side_toolbar": true,
            "hide_top_toolbar": false,
            "show_popup_button": true,
            "container_id": div,
            });
        }

        const TOTAL_STOCKS = 30;
        function create_tv_grid() {
            for(var i = 0; i < syms.length && i < TOTAL_STOCKS; i++) {
                const id = 'tv' +　i.toString()
                create_tv(id, syms[i]);
            }
            for (var i=syms.length; i < TOTAL_STOCKS; i++) {
                const id = 'tv' +　i.toString()
                document.getElementById(id).innerHTML = "";
            }
        }

    if (typeof TradingView === 'undefined') {
        var script = document.createElement('script');
        script.onload = create_tv_grid
        script.src = "https://s3.tradingview.com/tv.js";
        document.head.appendChild(script);
    } else {
        create_tv_grid()
    }

    return ''
    }
    """,
    Output(component_id='null', component_property='children'),
    Input('symbols', 'children')
)


def get_sym(row):
    return row['交易所'] + ':' + row['商品代码']

def get_position(row):
    return {'symbol': row['交易所'] + ':' + row['商品代码'], 'volume': row['持有数量']}


def get_crypts():
    cryp_df = utils.read_latest_csv('crypto')

    cryp_df = cryp_df[cryp_df['说明'].str.endswith(
        'US Dollar (calculated by TradingView)')]
    # print(cryp_df)
    cryptos = cryp_df.sort_values(
        by=['市场价值'], ascending=False).head(n_col*n_row)
    results = cryptos.apply(get_sym, axis=1).to_list()
    print(results)
    return (results)

def get_favorite():
    #fav_df = pd.read_csv('data/favorite.csv', dtype={'code':'string'}, delimiter=',', index_col=False)
    return fav_df['code'].values

def get_cfd():
    return ['OANDA:XAUUSD', 'OANDA:XAGUSD', 'OANDA:EURUSD', 'OANDA:WTICOUSD']


@app.callback(
    Output('pages-div', 'children'),
    Input('tabs', 'active_tab'),
    Input('SortBy', 'value'),
    Input('opts', 'value'),)
def select_industry(tab, sortby, opts):
    global stocks
    
    print('selected tab', tab, sortby, opts)
    if tab is None:
        return ''

    if tab == '加密货币':
        stocks = get_crypts()
    elif tab == '期货':
        stocks = get_cfd()
    elif tab == '自选':
        stocks = get_favorite()
    elif tab == '持有':
        mylist = pd.read_csv('data/my-list.csv',
                             dtype={'商品代码': 'string'}, delimiter=',')
        stocks = mylist.apply(get_sym, axis=1).to_list()
        # print('positions:', stocks)
    else:
        stocks = df[df['行业']==tab]
        if 'decending' in opts:
            stocks = stocks.sort_values(by=sortby, ascending=True)
        else:
            stocks = stocks.sort_values(by=sortby, ascending=False)
        stocks = stocks.apply(get_sym, axis=1).to_list()

    n_pages = (len(stocks) + n_col*n_row - 1)//(n_col*n_row)
    print('len(stocks)//(n_col*n_row)=', len(stocks)//(n_col*n_row))
    pages_children = ''
    active_page = '1'
    # if tab in page_state and 'page' in page_state[tab]:
    #     active_page = page_state[tab]['page']
    pages_children = dbc.Tabs([dbc.Tab(label=str(x), tab_id=str(x)) for x in range(1, n_pages+1)],
        id="tab_pages", active_tab=active_page)

    if tab != '持有' and tab != '自选':
        page_state['tab'] = tab
        save_json()
    
    return pages_children

@app.callback(
    [Output('div-tv', 'children'), 
    Output('symbols', 'children')],
    Input('tab_pages', 'active_tab'))
def select_page(page_str):
    global stocks_page
    if page_str is None:
        page_str = page_state[page_state['tab']]['page']

    page = int(page_str)
    

    n_pages = (len(stocks) + n_col*n_row - 1)//(n_col*n_row)
    if page > n_pages:
        print('invalid page')
        return ''
    
    page_state[page_state['tab']] = {"page": page_str}
    save_json()
    print('selected page', page)
    start = n_col*n_row*(page-1)
    stocks_page = stocks[start:start+n_col*n_row]
    return [create_tv(stocks_page), ','.join(stocks[start:start+n_col*n_row])]
    # return 

def addStock(stock):
    if stock in fav_df['code'].values:
        return
    fav_df.loc[len(fav_df.index)] = [stock]
    print('added stock', stock)
    fav_df.to_csv('data/favorite.csv', index=False)

def delStock(stock):
    global fav_df
    if stock not in fav_df['code'].values:
        return

    fav_df = fav_df[fav_df.code != stock]
    print('deleted stock', stock)
    fav_df.to_csv('data/favorite.csv', index=False)

@app.callback(
    Output('handlers', 'children'),
    [Input({'type': 'Add', 'index': ALL}, 'n_clicks'),
    Input({'type': 'Del', 'index': ALL}, 'n_clicks')])
def handler(*args):
    trigger = callback_context.triggered[0]
    try:
        obj = json.loads(trigger['prop_id'].split('.')[0])
        if obj['type'] == 'Add':
            print('addstock', obj['index'], stocks_page)
            addStock(stocks_page[obj['index']])
        elif obj['type'] == 'Del':
            print('delStock', obj['index'], stocks_page)
            delStock(stocks_page[obj['index']])
        # action_handler(obj['type'], syms[obj['index']], trigger['value'])
    except ValueError as e:
        return

@app.callback(
    Output('tabs-div', 'children'),
    Input('header', 'children'))
def select_tab(children):
    return dbc.Tabs(
        [
            dbc.Tab(label=x, tab_id=x) for x in industries
        ],
        id="tabs",
        active_tab=page_state['tab']
    )

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8888,
                   dev_tools_ui=True, dev_tools_props_check=True)
