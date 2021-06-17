import pandas as pd
import yfinance as yf
import mplfinance as mpf
import matplotlib as mpl
import matplotlib.pyplot as plt
from pychart import figure_pz, PanAndZoom

df = yf.Ticker('002167.SZ').history(period='max')

# s = mpf.make_mpf_style(base_mpf_style='yahoo', rc={'font.family': 'SimHei'})
kwargs = {
        "type": 'candle',
        "xrotation": 0,
        "volume": True,
        "title": "stock",
        "ylabel": "",
        "ylabel_lower": "",
        "tight_layout": True,
        "returnfig": True,
        "mav":(250),
        #"style":s,
    }

# mpl.rcParams['toolbar'] = 'None'
mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False
    
fig, axlist = mpf.plot(df, **kwargs)
fig.pan_zoom = PanAndZoom(fig)
plt.show()