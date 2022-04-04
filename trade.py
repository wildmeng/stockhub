# coding=utf-8
from gm.api import *
from gm.enum import MODE_BACKTEST, MODE_LIVE, OrderSide_Sell
import numpy as np
import pandas as pd
import utils
import json
import datetime
import time
import os
import sys
import logging
import psutil
from loguru import logger


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
    if context.account() is None:
        print('failed to get account')
        sys.exit()

    cash = context.account().cash
    if cash is None or cash.nav == 0:
        print('failed to get cash')
        sys.exit()
    
    context.stocks = utils.MyStocks()

    positions = context.account().positions()
    allSymbols = []
    for pos in positions:
        context.stocks.update(pos['symbol'], '可用数量', int(pos['available_now']))
        context.stocks.update(pos['symbol'], '持有市值', int(pos['market_value']))
        allSymbols.append(pos['symbol'])

    syms = context.stocks.getAllSymbols()
    for sym in syms:
        if sym not in allSymbols:
            context.stocks.update(sym, '可用数量', 0)
            context.stocks.update(sym, '持有市值', 0)
    context.stocks.flush()

    # do_subscribe(context)

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

def trade_order(context, order_name):
    global gsymbol, gcontext

    if not isTradingDay(context):
        return
    updateStocks(context)
    logger.info(order_name)
    context.stocks = utils.MyStocks()
    
    lst = context.stocks.getOrder(order_name)
    logger.info(str(lst))
    for l in lst:
        gsymbol = l[0]
        code = l[1]
        if not isinstance(code, str):
            logger.error('invalid command:', code)
            continue

        update_p()
        is_num = code.replace('.', '', 1).isdigit()
        if order_name == 'stop':
             if (is_num and p < float(code)) or (not is_num and eval(code) == True):
                logger.info(f'stopping order {gsymbol}')
                order = order_target_percent(symbol=gsymbol, percent=0,
                    position_side=PositionSide_Long, order_type=OrderType_Market, price=0)
                logger.info(f'stopped order result:{order}')
                context.stocks.update(gsymbol, 'stop', '# ' + code)
        elif order_name == 'target':
             if (is_num and p >= float(code)) or (not is_num and eval(code) == True):
                logger.info('targeting order {gsymbol}')
                order = order_target_percent(symbol=gsymbol, percent=0,
                    position_side=PositionSide_Long, order_type=OrderType_Market, price=0)
                logger.info('targetted order result: {order}')
                context.stocks.update(gsymbol, 'target', '# ' + code)
        else :
            logger.info('executing {}', code)
            eval(code)
            context.stocks.update(gsymbol, order_name, '# ' + code)

    context.stocks.flush()
    time.sleep(2)
    updateStocks(context)

def init(context):
    logger.add("file_trade.log")
    
    updateStocks(context)
    logger.info('started')
    schedule(schedule_func=cleanTA, date_rule='1d', time_rule='09:00:10')
    schedule(schedule_func=lambda ctx: trade_order(ctx, 'open'), date_rule='1d', time_rule='09:35:00')
    targets_time = ['09:33:00', '09:53:00', '10:53:00', '13:53', '14:53:00']
    for t in targets_time:
        schedule(schedule_func=lambda ctx: trade_order(ctx, 'target'), date_rule='1d', time_rule=t)

    schedule(schedule_func=lambda ctx: trade_order(ctx, 'close'), date_rule='1d', time_rule='14:50:00')
    schedule(schedule_func=lambda ctx: trade_order(ctx, 'stop'), date_rule='1d', time_rule='14:55:00')

def on_order_status(context, order):
    logger.info('order status: {} {} {}', order.symbol, order.status, order.volume)
    if order.status == OrderStatus_Filled:
        updateStocks(context)

def update_p():
    global p
    tick = history_n(symbol=gsymbol, frequency='tick', adjust=ADJUST_PREV, count=1)
    price = tick[0]['price']
    if price is None or price == 0:
        logger.error("invalid price", price)
        sys.exit()
    
    p = price
    logger.info(f'price {gsymbol}: {p}')
    
def pma(N=60, n=14):
    return (p - ma(N))/atr(n)
    
def ma(N):
    ma_id = gsymbol + str(N)
    if ma_id in gmabuf:
        return gmabuf[ma_id]
        
    dailybars = history_n(symbol=gsymbol, frequency='1d', adjust=ADJUST_PREV, fields='close', count=N)
    if len(dailybars) != N:
        logger.error("history_n failed")
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
        logger.error("history_n failed")
        sys.exit()
        
    atr = [(max(bars[i]['high'], bars[i-1]['close']) - min(bars[i]['low'], bars[i-1]['close'])) for i in range(1, N+1)]
    res = sum(atr)/len(atr)
    gatrbuf[atr_id] = res
    return res

def buy_percent(percent):
    logger.info('{gsymbol}, {percent}')
    order = order_percent(symbol=gsymbol, percent=percent/100.0,
                side=OrderSide_Buy, order_type=OrderType_Market, position_effect=PositionEffect_Open, price=0)

def buy_target(percent):
    logger.info('{gsymbol}, {percent}')
    order = order_target_percent(symbol=gsymbol, percent=percent/100.0,
                position_side=PositionSide_Long, order_type=OrderType_Market, price=0)

def buy_vol(vol):
    logger.info(f'{gsymbol}, {vol}')
    order = order_volume(symbol=gsymbol, volume=vol, side=OrderSide_Buy, order_type=OrderType_Market, position_effect=PositionEffect_Open)

def buy_val(val):
    logger.info(f'{gsymbol}, {val}')
    order = order_value(symbol=gsymbol, value=val, side=OrderSide_Buy, order_type=OrderType_Market, position_effect=PositionEffect_Open)
    
def sell_vol(vol):
    logger.info(f'{gsymbol}, {vol}')
    order = order_volume(symbol=gsymbol, volume=vol, side=OrderSide_Sell, order_type=OrderType_Market, position_effect=PositionEffect_Close)
def sell_val(val):
    logger.info(f'{gsymbol}, {val}')
    order = order_value(symbol=gsymbol, value=val, side=OrderSide_Sell, order_type=OrderType_Market, position_effect=PositionEffect_Close)

if __name__ == '__main__':

    # if "cfgm3.exe" not in (p.name() for p in psutil.process_iter()):
    #     time.sleep(60)
    #     os.startfile("C:\\Users\\xiaof\\AppData\\Roaming\\ChinaFortune Goldminer3\\cfgm3.exe")
    #     time.sleep(60)

    run(strategy_id='73058cee-7c3f-11ec-be08-d8cb8a016c6b',
        filename='trade.py',
        mode=MODE_LIVE,
        token='0147eee0d2783671c80d7a618d3fa7a6cc7c9778',)


