
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, ALL
from dash_html_components.Script import Script
import dash_bootstrap_components as dbc
from dash import callback_context
import utils
import numpy as np
import pandas as pd
import json

n_col = 3
n_row = 20

tabs_name = '行业'
df = utils.read_latest_csv()
jq_industry = pd.read_csv('data/jq-industries.csv', sep=':')
industries = jq_industry['name'].unique()

industries = np.append(industries, ['加密货币', '期货', '持有'])
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=False)

tv_style={'width': '96%', 'height':'350px', 'marginLeft': '2%', "marginRight": "2%"}

tabs = dbc.Tabs(
            [
                dbc.Tab(label=x, tab_id=x)  for x in industries
            ],
            id="tabs",
            active_tab= industries[0] #'持有'# industries[0],
        )
def cell(row, col):
    id = (row-1)*n_col + (col-1)
    div = html.Div(id=f'div{id}', children='')
    return html.Div(children=[div,
    html.Div(id=f"tv{id}", style=tv_style)])

rows = [
        dbc.Row(
            [
                dbc.Col(cell(row, col)) for col in range(1, n_col+1)
            ],
            align="top",
            no_gutters = True,
        ) for row in range(1, n_row+1) ]

app.layout = dbc.Container( [tabs] + rows + [html.Div(id='null', style={'height':'10px'}),
        html.Div(id='symbols', style={'display':'none'}),
        html.Div(id='handlers', style={'display':'none'})], fluid=True,
)

app.clientside_callback(
    """
    function(symbols) {
        console.log('symbols', symbols);
        const syms = symbols.split(',')

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
            "range": "24M",
            "details": false,
            "allow_symbol_change": false,
            "hide_side_toolbar": true,
            "hide_top_toolbar": false,
            "show_popup_button": true,
            "container_id": div,
            });
        }

        function create_tv_grid() {
            for(var i = 0; i < syms.length; i++) {
                const id = 'tv' +　i.toString()
                create_tv(id, syms[i]);
            }
            for (var i=syms.length; i < 60; i++) {
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
    return {'symbol' : row['交易所'] + ':' + row['商品代码'], 'volume': row['持有数量']}

def get_crypts():
    cryp_df = utils.read_latest_csv('crypto')
    
    cryp_df = cryp_df[cryp_df['说明'].str.endswith('US Dollar (calculated by TradingView)')]
    print(cryp_df)
    cryptos = cryp_df.sort_values(by=['市场价值'], ascending=False).head(n_col*n_row)
    results = cryptos.apply(get_sym, axis=1).to_list()

    return (results)

def get_cfd():
    return ['OANDA:XAUUSD','OANDA:XAGUSD','OANDA:EURUSD','OANDA:WTICOUSD']

all_ouputs = [Output('symbols', 'children')] + [Output(f'div{i}', 'children') for i in range(n_col*n_row)]

def get_pos_div(i, row):
    #vol = row['持有数量']
    value = int(row['持有市值'])
    return [html.Label(f'{value}%'),
    html.Label('调仓至: ', style={"margin-left": "15px"}), 
    dcc.Input(id={'type':'change', 'index':i}, type='number', value=row['调仓至'],style={'width':'10%'}),
    html.Label('%'),
    html.Label('目标价: ', style={"margin-left": "15px"}),
    dcc.Input(id={'type':'target', 'index':i}, type='number', value=row['目标价'],style={'width':'10%'}),
    html.Label('止损价: ', style={"margin-left": "15px"}), 
    dcc.Input(id={'type':'stoploss', 'index':i}, type='number', value=row['止损价'],style={'width':'10%'}),
    html.Button('删除', id={'type':'delete', 'index':i}, style={"margin-left": "15px"})]

@app.callback(
    all_ouputs,
    Input('tabs', 'active_tab'),)
def select_industry(tab):
    if tab is None:
        return ''

    print('selected tab', tab)

    if tab == '加密货币':
        stocks = get_crypts()
    elif tab == '期货':
        stocks = get_cfd()
    elif tab == '持有':
        mylist = pd.read_csv('data/my-list.csv', dtype={'商品代码':'string'}, delimiter=',')
        print(mylist)
        stocks = mylist.apply(get_sym, axis=1).to_list()
        print('positions:', stocks)
    else:
        stocks = jq_industry[jq_industry['name'] == tab]['symbols'].iloc[0].split(',')
        stocks = map(lambda x: x.split('.')[0], stocks)
        stocks = df[df['商品代码'].isin(stocks)]
        stocks = stocks.sort_values(by=['RSI(14)'], ascending=False).head(n_col*n_row)
        stocks = stocks.apply(get_sym, axis=1).to_list()

    divs = []
    if tab == '持有':
        for idx, row in mylist.iterrows():
            divs.append(get_pos_div(idx, row))
    else:
        for i, v in enumerate(stocks):
            divs.append(html.Button('加入自选', id={'type':'add', 'index':i}))
    
    divs += [''] * (n_col*n_row-len(divs))
    return [','.join(stocks)] + divs

def action_handler(action, symbol, value):
    print(action, symbol, value)
    stocks = utils.MyStocks()
    if action == 'change':
        stocks.update(symbol, '调仓至', value)
    elif action == 'target':
        stocks.update(symbol, '目标价', value)
    elif action == 'stoploss':
        stocks.update(symbol, '止损价', value)
    elif action == 'add':
        stocks.addStock(symbol)
    elif action == 'delete':
        stocks.delStock(symbol)
    else:
        print('unknow action', action)
        return

    stocks.flush()

@app.callback(
    Output('handlers', 'children'),
    [Input({'type': 'change', 'index': ALL}, 'value'),
    Input({'type': 'target', 'index': ALL}, 'value'),
    Input({'type': 'stoploss', 'index': ALL}, 'value'),
    Input({'type': 'add', 'index': ALL}, 'n_clicks'),
    Input({'type': 'delete', 'index': ALL}, 'n_clicks'),
    Input('symbols', 'children')])
def handler(*args):
    #print(args)
    syms = args[-1].split(',')
    trigger = callback_context.triggered[0]
    print(trigger)
    try:
        obj = json.loads(trigger['prop_id'].split('.')[0])
        action_handler(obj['type'], syms[obj['index']], trigger['value'])
    except ValueError as e:
        return
    
if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8888,dev_tools_ui=True,dev_tools_props_check=True)
