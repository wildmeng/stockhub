# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *
from gm.enum import MODE_LIVE, OrderSide_Sell
import numpy as np
import pandas as pd
import utils
import json
import datetime
import time

def isTradingDay(context):
    today = datetime.date.today()
    start = today.strftime("%Y-%m-%d")
    next = datetime.datetime.now() + datetime.timedelta(days=1)
    end = next.strftime("%Y-%m-%d")
    
    dates = get_trading_dates(exchange='SZSE',	start_date=start,	end_date=end)
    if start in dates:
        return True
    else:
        return False

def updateStocks(context):

    context.stocks = utils.MyStocks()
    cash = context.account().cash
    if cash.nav == 0:
        print('failed to get account')
        return
    positions = context.account().positions()
    allSymbols = []
    for pos in positions:
        context.stocks.update(pos['symbol'], '可用数量', int(pos['available_now']))
        context.stocks.update(pos['symbol'], '持有市值', int(pos['market_value']*100/cash.nav))
        allSymbols.append(pos['symbol'])

    syms = context.stocks.getAllSymbols()
    for sym in syms:
        if sym not in allSymbols:
            context.stocks.update(sym, '可用数量', 0)
            context.stocks.update(sym, '持有市值', 0)
    context.stocks.flush()

def init(context):
    updateStocks(context)
    schedule(schedule_func=trade, date_rule='1d', time_rule='13:35:00')
    schedule(schedule_func=updateStocks, date_rule='1d', time_rule='15:00:00')
    schedule(schedule_func=do_subscribe, date_rule='1d', time_rule='09:30:00')
    schedule(schedule_func=do_unsubscribe, date_rule='1d', time_rule='15:29:00')

def on_order_status(context, order):
    print('order status:')
    print(order)
    if order.status == OrderStatus_Filled:
        do_subscribe(context)
        updateStocks(context)

def do_unsubscribe(context):
    if not isTradingDay(context):
        print('not trading day')
        return
    unsubscribe(symbols='*', frequency='tick')
    
def do_subscribe(context):
    if not isTradingDay(context):
        print('not trading day')
        return

    updateStocks(context)
    lst = context.stocks.getWatchList()
    if len(lst) == 0:
        unsubscribe(symbols='*', frequency='tick')
        return

    subscribe(symbols=','.join(lst), frequency='tick', unsubscribe_previous=True)

def	on_tick(context, tick):
    # print(tick)
    if tick['price'] == 0:
        return

    stop = context.stocks.get(tick['symbol'], '止损价')
    if not np.isnan(stop) and stop > 0:
        if tick['price'] <= stop:
            print('stop loss for ', tick['symbol'], stop, tick['price'])
            #order_target_percent(symbol=tick['symbol'], percent=0,
            #    position_side=PositionSide_Long, order_type=OrderType_Market, price=0)
    
    target = context.stocks.get(tick['symbol'], '目标价')
    if not np.isnan(target) and target > 0:
        if tick['price'] >= target:
            print('take profit for ', tick['symbol'], tick['price'], target)
            #order_target_percent(symbol=tick['symbol'], percent=0,
            #    position_side=PositionSide_Long, order_type=OrderType_Market, price=0)

def trade(context):
    if not isTradingDay(context):
        print('not trading day')
        return

    while True:
        print('executing trade orders')
        stocks = utils.MyStocks()
        changes = stocks.getChangeList()
        if len(changes) == 0:
            return
        for change in changes:
            sym = change[0]
            percent = int(change[1])/100.0
            print(sym, 'adjust target:', sym, percent*100, '%')
            result = order_target_percent(symbol=sym, percent=percent, position_side=PositionSide_Long,
                        order_type=OrderType_Market, price=0)
            print(result)
            if len(result) > 0 and (result[0].status == OrderStatus_Filled or result[0].volume == 0):
                stocks.update(sym, '调仓至', np.nan)
                stocks.flush()
                print('Successful')
        
        updateStocks(context)
        time.sleep(60)


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

