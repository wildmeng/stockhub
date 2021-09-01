# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *
from gm.enum import MODE_LIVE, OrderSide_Sell
import numpy as np
import pandas as pd
import utils
import json

def updateStocks(context):
    stocks = utils.MyStocks()
    cash = context.account().cash

    print('cash:', cash.market_value, cash.nav, cash.available)
    
    positions = context.account().positions()
    for pos in positions:
        stocks.update(pos['symbol'], '持有数量', int(pos['volume']))
        stocks.update(pos['symbol'], '持有市值', int(pos['market_value']*100/cash.nav))
    
    stocks.flush()
def init(context):
    # 每天14:50 定时执行algo任务,
    # algo执行定时任务函数，只能传context参数
    # date_rule执行频率，目前暂时支持1d、1w、1m，其中1w、1m仅用于回测，实时模式1d以上的频率，需要在algo判断日期
    # time_rule执行时间， 注意多个定时任务设置同一个时间点，前面的定时任务会被后面的覆盖 
    updateStocks(context)
    schedule(schedule_func=trade, date_rule='1d', time_rule='09:31:00')
    schedule(schedule_func=updateStocks, date_rule='1d', time_rule='09:00:00')
    schedule(schedule_func=updateStocks, date_rule='1d', time_rule='15:00:00')

def trade(context):
    stocks = utils.MyStocks()
    changes = stocks.getChangeList()
    for change in changes:
        sym = change[0]
        percent = int(change[1])/100.0
        print('ajust volume, ', sym, percent, '%')
        result = order_target_percent(symbol=sym, percent=percent, position_side=PositionSide_Long,
                    order_type=OrderType_Market, price=0)
        
        if result.Status == OrderStatus_Filled:
            stocks.update(sym, '调仓至', np.nan)
            print('Successful')

    stocks.flush()

if __name__ == '__main__':
    '''
        strategy_id策略ID, 由系统生成
        filename文件名, 请与本文件名保持一致
        mode运行模式, 实时模式:MODE_LIVE回测模式:MODE_BACKTEST
        token绑定计算机的ID, 可在系统设置-密钥管理中生成
        backtest_start_time回测开始时间
        backtest_end_time回测结束时间
        backtest_adjust股票复权方式, 不复权:ADJUST_NONE前复权:ADJUST_PREV后复权:ADJUST_POST
        backtest_initial_cash回测初始资金
        backtest_commission_ratio回测佣金比例
        backtest_slippage_ratio回测滑点比例
    '''
    run(strategy_id='fb042a02-00ad-11ec-891a-80ce622f6462',
        filename='trade.py',
        mode=MODE_LIVE,
        token='0147eee0d2783671c80d7a618d3fa7a6cc7c9778')

