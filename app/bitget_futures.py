import bitget_api_connect as api_connect
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytz


def get_futures_price(symbol):
    request_path = '/api/v2/mix/market/symbol-price'
    query = {'symbol': symbol, 'productType': 'USDT-FUTURES'}
    market_price = api_connect.bitget_request(request_path, None, query, "GET")
    return market_price.json().get('data')[0].get('price')


def get_futures_balance(symbol):
    request_path = '/api/v2/mix/account/account'
    query = {'symbol': symbol, 'productType': 'USDT-FUTURES', 'marginCoin': 'USDT'}
    balance = api_connect.bitget_request(request_path, None, query, "GET")
    return balance.json().get('data').get('available')


def get_futures_open_positions_info(symbol):
    request_path = '/api/v2/mix/position/single-position'
    query = {'productType': 'USDT-FUTURES', 'symbol': symbol, 'marginCoin': 'USDT'}
    open_positions = api_connect.bitget_request(request_path, None, query, "GET")
    return open_positions.json().get('data')


def set_leverage(symbol, leverage):
    request_path = '/api/v2/mix/account/set-leverage'
    payload = {'symbol': symbol, 'productType': 'USDT-FUTURES', 'marginCoin': 'USDT', 'leverage': leverage}
    api_connect.bitget_request(request_path, payload, {}, "POST")


def set_position_mode(position_mode):
    request_path = '/api/v2/mix/account/set-position-mode'
    # position modes - one_way_mode: one-way mode; hedge_mode: hedge mode
    payload = {'productType': 'USDT-FUTURES', 'posMode': position_mode}
    api_connect.bitget_request(request_path, payload, {}, "POST")


def get_estimated_open_size(symbol, marginCoin, leverage, prcnt_trade):
    request_path = '/api/v2/mix/account/open-count'
    query = {'symbol': symbol, 
             'productType': 'USDT-FUTURES', 
             'marginCoin': marginCoin, 
             'openAmount': str(float(get_futures_balance(symbol)) * float(prcnt_trade)),
             'openPrice': get_futures_price(symbol),
             'leverage': leverage
            }
    estimated_open_position_info = api_connect.bitget_request(request_path, None, query, "GET")
    return estimated_open_position_info.json().get('data').get('size')


def futures_market_order(prediction, marginCoin, symbol, leverage, prcnt_trade, position_mode):
    request_path = '/api/v2/mix/order/place-order'

    trade_size = get_estimated_open_size(symbol, marginCoin, leverage, prcnt_trade)
    order_direction = lambda : 'buy' if prediction == 1 else 'sell'

    payload = {'symbol': symbol, 
               'productType': 'USDT-FUTURES', 
               'marginMode': 'isolated',
               'marginCoin': marginCoin,
               'size': trade_size,
               'side': order_direction(),
               'orderType': 'market',
              }
    
    #set position_mode 
    set_position_mode(position_mode)

    # set leverage before opening a position
    set_leverage(symbol, leverage)

    # open position
    place_order = api_connect.bitget_request(request_path, payload, {}, "POST")
    return place_order.json()


def futures_close_position(symbol):
    request_path = '/api/v2/mix/order/close-positions'
    payload = {'symbol': symbol, 'productType': 'USDT-FUTURES'}
    close_open_position = api_connect.bitget_request(request_path, payload, {}, "POST")
    return close_open_position.json()


def futures_SLTP_orders(symbol, marginCoin, prediction, sltp_prcnt, type):
    request_path = '/api/v2/mix/order/place-tpsl-order'
    open_price = float(get_futures_open_positions_info('SUIUSDT')[0].get('openPriceAvg'))
    check_scale_value = abs(Decimal(get_futures_price(symbol)).as_tuple().exponent)
    
    if type.upper()=='TP':
        trigger_price = open_price * (1 + float(sltp_prcnt)) if prediction == 1 else open_price * (1 - float(sltp_prcnt))
    else:
        trigger_price = open_price * (1 - float(sltp_prcnt)) if prediction == 1 else open_price * (1 + float(sltp_prcnt))

    hold_side = 'buy' if prediction == 1 else 'sell'

    payload = {'marginCoin': marginCoin, 
               'productType': 'USDT-FUTURES', 
               'symbol': symbol, 
               'planType': 'pos_profit' if type.upper() == 'TP' else 'pos_loss', 
               'triggerPrice': round(trigger_price, check_scale_value),
               'holdSide': hold_side
               }

    stop_loss = api_connect.bitget_request(request_path, payload, {}, "POST")
    return stop_loss.json()


def futures_cancel_open_orders(symbol):
    request_path = '/api/v2/mix/order/cancel-plan-order'
    pos_dict = {'sl_order': 'pos_loss', 'tp_order': 'pos_profit'}
    for order_type, pos in pos_dict.items():
        payload = {'symbol': symbol, 'productType': 'USDT-FUTURES', 'planType': pos}
        cancel_open_orders = api_connect.bitget_request(request_path, payload, {}, "POST")
        pos_dict[order_type] = cancel_open_orders.json()
    return pos_dict


def is_open_position_valid(symbol):
    request_path = '/api/v2/mix/position/history-position'

    prev_date = datetime.now() - timedelta(days=1)
    unix_timestamp = str(int((prev_date.replace(hour=0,minute=0,second=0,microsecond=0)).timestamp() * 1000))
    trades_query = {'symbol': symbol, 'productType': 'USDT-FUTURES', 'startTime': unix_timestamp}
    response_json = api_connect.bitget_request(request_path, None, trades_query, "GET").json()

    last_trade_timestamp = response_json.get('data').get('list')[0].get('utime')
    timestamp_s = float(last_trade_timestamp) / 1000

    converted_time_hr = datetime.fromtimestamp(timestamp_s, tz=timezone.utc).astimezone(pytz.timezone('Asia/Manila')).hour

    now_utc = datetime.now(pytz.utc)
    manila_time = now_utc.astimezone(pytz.timezone('Asia/Manila')).hour - 1

    return True if converted_time_hr>=manila_time else False