# coding=utf-8
from gm.api import *
from gm.enum import MODE_BACKTEST, MODE_LIVE, OrderSide_Sell
import numpy as np
import pandas as pd
import utils
import json
import datetime
import time
import psutil
import os
import sys
import logging
import math

gcontext = None
gsymbol = None
p = None

gmabuf = {}
gatrbuf = {}

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
    if context.account() is None or cash.nav == 0:
        logging.info('failed to get account')
        sys.exit()

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

    do_subscribe(context)

    return True

def in_trade_hour(context):
    now = datetime.datetime.now()
    if now.hour >= 15 or now.hour < 9:
        return False

    if now.hour == 9 and now.minute < 30 :
        return False

    return True

def cleanTA(context):
    global gatrbuf, gmabuf, p
    gatrbuf = {}
    gmabuf = {}
    p = 0
    
def init(context):
    updateStocks(context)
    do_stop(context)
    schedule(schedule_func=cleanTA, date_rule='1d', time_rule='09:00:00')
    schedule(schedule_func=trade, date_rule='1d', time_rule='14:50:00')

    #schedule(schedule_func=do_subscribe, date_rule='1d', time_rule='09:30:00')
    #schedule(schedule_func=do_unsubscribe, date_rule='1d', time_rule='14:58:00')

def on_order_status(context, order):
    logging.info('order status:')
    logging.info(order)
    if order.status == OrderStatus_Filled:
        updateStocks(context)

def update_p():
    global p
    tick = history_n(symbol=gsymbol, frequency='tick', adjust=ADJUST_PREV, count=1)
    price = tick[0]['price']
    if price is None or price == 0:
        logging.error("invalid price", price)
        sys.exit()
    
    p = price
    
def ma(N):
    ma_id = gsymbol + str(N)
    if ma_id in gmabuf:
        return gmabuf[ma_id]
        
    dailybars = history_n(symbol=gsymbol, frequency='1d', adjust=ADJUST_PREV, fields='close', count=N)
    if len(dailybars) != N:
        logging.error("history_n failed")
        sys.exit()
        
    closes = [x['close'] for x in dailybars]
    avr = sum(closes) / len(closes)
    gmabuf[ma_id] = avr
    return avr

def atr(N=14):
    atr_id = gsymbol + str(N)
    if atr_id in gatrbuf:
        return gatrbuf[atr_id]
        
    bars = history_n(symbol=gsymbol, frequency='1d', adjust=ADJUST_PREV, fields='high,low,close', count=N+1)
    if len(bars) != N+1:
        logging.error("history_n failed")
        sys.exit()
        
    atr = [(max(bars[i]['high'], bars[i-1]['close']) - min(bars[i]['low'], bars[i-1]['close'])) for i in range(1, N+1)]
    res = sum(atr)/len(atr)
    gatrbuf[atr_id] = res
    return res

def do_stop(context):
    global gsymbol, gcontext
    if not isTradingDay(context):
        return

    lst = context.stocks.getWatchList()
    for l in lst:
        if not isinstance(l[1], str) and not isinstance(l[2], str):
            continue
        gsymbol = l[0]
        update_p()
        if (isinstance(l[1], str) and eval(l[1]) == True) or (isinstance(l[2], str) and eval(l[2]) == True):
            logging.info('stopped trading for', l[0], l[1], l[2])
            order = order_target_percent(symbol=gsymbol, percent=0,
                position_side=PositionSide_Long, order_type=OrderType_Market, price=0)
            logging.info('order:', order)

def buy(percent):
    order = order_percent(symbol=gsymbol, percent=percent/100.0,
                side=OrderSide_Buy, order_type=OrderType_Market, position_effect=PositionEffect_Open, price=0)
    logging.info('buy order:', order)

def target(percent):
    order = order_target_percent(symbol=gsymbol, percent=percent/100.0,
                position_side=PositionSide_Long, order_type=OrderType_Market, price=0)
    logging.info('target order:', order)
    
def do_unsubscribe(context):
    return
    if not isTradingDay(context):
        logging.info('not trading day')
        return
    unsubscribe(symbols='*', frequency='tick')

def do_subscribe(context):
    return
    if not isTradingDay(context):
        logging.info('not trading day')
        return

    lst = context.stocks.getWatchList()
    if len(lst) == 0:
        unsubscribe(symbols='*', frequency='tick')
        return

    subscribe(symbols=','.join(lst), frequency='tick', unsubscribe_previous=True)

def	on_tick(context, tick):
    # logging.info(tick)
    # if tick['price'] == 0:
    #     return

    # stop = context.stocks.get(tick['symbol'], '止损价')
    # if not np.isnan(stop) and stop > 0:
    #     if tick['price'] <= stop:
    #         logging.info('stop loss for ', tick['symbol'], stop, tick['price'])
    #         order_target_percent(symbol=tick['symbol'], percent=0,
    #             position_side=PositionSide_Long, order_type=OrderType_Market, price=0)

    # target = context.stocks.get(tick['symbol'], '目标价')
    # if not np.isnan(target) and target > 0:
    #     if tick['price'] >= target:
    #         logging.info('take profit for ', tick['symbol'], tick['price'], target)
    #         order_target_percent(symbol=tick['symbol'], percent=0,
    #             position_side=PositionSide_Long, order_type=OrderType_Market, price=0)
    pass

def trade(context):
    if not isTradingDay(context):
        logging.info('not trading day')
        return
    if not in_trade_hour(context):
        logging.info('not trading hour')
        return

    logging.info('executing trade orders')
    stocks = utils.MyStocks()
    changes = stocks.getChangeList()
    if len(changes) == 0:
        return
    for change in changes:
        sym = change[0]
        percent = int(change[1])/100.0
        logging.info(sym, 'adjust target:', sym, percent*100)
        result = order_target_percent(symbol=sym, percent=percent, position_side=PositionSide_Long,
                    order_type=OrderType_Market, price=0)
        logging.info(result)
        if len(result) > 0 and (result[0].status == OrderStatus_Filled or result[0].volume == 0):
            stocks.update(sym, '调仓至', np.nan)
            stocks.flush()
            logging.info('Successful')

    updateStocks(context)


def on_order_status_v2(context, order):
    # type: (Context, Order) -> NoReturn
    """
    委托状态更新事件. 参数order为委托信息
    响应委托状态更新事情，下单后及委托状态更新时被触发
    3.0.113 后增加.
    与on_order_status 具有等同含义, 在二者都被定义时(当前函数返回类型为类，速度更快，推介使用), 只会调用 on_order_status_v2
    """
    pass

def on_execution_report_v2(context, execrpt):
    # type: (Context, ExecRpt) -> NoReturn
    """
    委托执行回报事件. 参数 execrpt 为执行回报信息
    响应委托被执行事件，委托成交后被触发
    3.0.113 后增加
    已 on_execution_report 具有等同含义, 在二者都被定义时(当前函数返回类型为类，速度更快，推介使用), 只会调用 on_execution_report_v2
    """
    pass


def on_account_status_v2(context, account_status):
    # type: (Context, AccountStatus) -> NoReturn
    """
    交易账户状态变更事件. 仅响应 已连接，已登录，已断开 和 错误 事件
    account_status: 包含account_id(账户id), account_name(账户名),ConnectionStatus(账户状态)
    3.0.113 后增加
    已 on_account_status 具有同等意义, 在二者都被定义时(当前函数返回类型为类，速度更快，推介使用), 只会调用 on_account_status_v2
    """
    pass


def on_trade_data_connected(context):
    # type: (Context) -> NoReturn
    """
    交易通道网络连接成功事件
    """

    trade(context)


def on_market_data_connected(context):
    # type: (Context) -> NoReturn
    """
    实时行情网络连接成功事件
    """
    pass


def on_market_data_disconnected(context):
    # type: (Context) -> NoReturn
    """
    实时行情网络连接断开事件
    """
    pass


def on_trade_data_disconnected(context):
    # type: (Context) -> NoReturn
    """
    交易通道网络连接断开事件
    """
    pass

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

    logging.info('trade is started')
    if "cfgm3.exe" not in (p.name() for p in psutil.process_iter()):
        os.startfile("C:\\Users\\xiaof\\AppData\\Roaming\\ChinaFortune Goldminer3\\cfgm3.exe")
        time.sleep(60)

    run(strategy_id='0bce617c-471f-11ec-b609-00fffac243b5',
        filename='trade.py',
        mode=MODE_LIVE,
        token='0147eee0d2783671c80d7a618d3fa7a6cc7c9778',)


