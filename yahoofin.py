
import pandas as pd
import pandas_ta as ta
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

df = yf.Ticker('000002.SZ').history(period='5y')

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.01)

main_fig = go.Candlestick(x=df.index,
            open=df.Open,
            high=df.High,
            low=df.Low,
            close=df.Close)
fig.add_trace(main_fig, row=1, col=1)
fig.update_layout(xaxis_rangeslider_visible=False, 
        dragmode='pan')
fig.update_yaxes(fixedrange=True)

rsi = ta.rsi(df["Close"], length=14)

last = df[-10:]
idx_min = last.Close.idxmin()
print(last.index.get_loc(idx_min))
idx_max = last.Close.idxmax()
print(last.index.get_loc(idx_max))
print(last)
rsi_fig = go.Scatter(x=df.index, y=rsi, line=dict(color='blue', width=1))


fig.add_trace(rsi_fig, row=2, col=1)


fig.add_hline(y=30, row=2, line_dash="dash", line_color="green")
fig.add_hline(y=70, row=2, line_dash="dash", line_color="red")
#fig.update_layout(height=800, width=1200, hoverdistance=0, title_text="Stock")

fig.add_vrect(x0="2021-01-31", x1="2021-04-04", 
              annotation_text="decline", annotation_position="top left",
              fillcolor="green", opacity=0.25, line_width=0)

fig.show()