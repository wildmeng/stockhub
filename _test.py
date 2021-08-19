
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash_html_components.S import S
from dash_html_components.Script import Script
import dash_bootstrap_components as dbc
import utils
import numpy as np
import pandas as pd

n_col = 3
n_row = 20

tabs_name = '行业'
df = utils.read_latest_csv()
jq_industry = pd.read_csv('data/jq-industries.csv', sep=':')
industries = jq_industry['name'].unique()

industries = np.append(industries, ['加密货币', '期货', '自选'])
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

tv_style={'width': '96%', 'height':'350px', 'marginLeft': '2%', "marginRight": "2%"}


tabs = dbc.Tabs(
            [
                dbc.Tab(label=x, tab_id=x)  for x in industries
            ],
            id="tabs",
            active_tab= '自选'# industries[0],
        )

rows = [
        dbc.Row(
            [
                dbc.Col(html.Div(id=f"tv{row}{col}", style=tv_style)) for col in range(1, n_col+1)
            ],
            align="top",
            no_gutters = True,
        ) for row in range(1, n_row+1) ]

app.layout = dbc.Container( [tabs] + rows + [html.Div(id='null', style={'height':'10px'}),
        html.Div(id='symbols', style={'display':'none'})], fluid=True,
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
                const id = 'tv' + (Math.floor(i/3) + 1).toString() + (i%3 + 1).toString()
                console.log(id, syms[i])
                create_tv(id, syms[i]);
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

def get_crypts():
    cryp_df = utils.read_latest_csv('crypto')
    print('get_crypts')
    
    cryp_df = cryp_df[cryp_df['说明'].str.endswith('US Dollar (calculated by TradingView)')]
    print(cryp_df)
    cryptos = cryp_df.sort_values(by=['市场价值'], ascending=False).head(n_col*n_row)
    results = cryptos.apply(get_sym, axis=1).to_list()
    print(results)

    return ','.join(results)

def get_my_list():
    mylist = pd.read_csv('data/my-list.csv', dtype={'商品代码':'string'}, delimiter=':')
    print('get_my_list')
    
    print(mylist)
    results = mylist.apply(get_sym, axis=1).to_list()
    print(results)

    return ','.join(results)

def get_cfd():
    mylist = 'OANDA:XAUUSD,OANDA:XAGUSD,OANDA:EURUSD,OANDA:WTICOUSD'
    return mylist

@app.callback(
    Output('symbols', 'children'),
    Input('tabs', 'active_tab'),)  
def select_industry(tab):
    if tab is None:
        return ''

    if tab == '加密货币':
        return get_crypts()
    elif tab == '期货':
        return get_cfd()
    elif tab == '自选':
        return get_my_list()

    print('selected tab', tab)
    stocks = jq_industry[jq_industry['name'] == tab]['symbols'].iloc[0].split(',')
    stocks = map(lambda x: x.split('.')[0], stocks)
    stocks = df[df['商品代码'].isin(stocks)]
    print(stocks)
    stocks = stocks.sort_values(by=['RSI(14)'], ascending=False).head(n_col*n_row)

    stocks = stocks.apply(get_sym, axis=1).to_list()
    print(stocks)

    return ','.join(stocks)

if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=80)
