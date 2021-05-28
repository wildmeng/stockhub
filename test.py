from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5

# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()

# request connection status and parameters
# print(mt5.terminal_info())
# get data on MetaTrader 5 version
# print(mt5.account_info())


symbols = mt5.symbols_get()
for a in symbols:
    rates = mt5.copy_rates_from_pos(a.name, mt5.TIMEFRAME_D1, 0, 1000,)
    rates_frame = pd.DataFrame(rates)
    print('downloaded', a.name, len(rates_frame))
