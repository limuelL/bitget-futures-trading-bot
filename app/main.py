from dotenv import load_dotenv
import data_processing as dp
import bitget_futures as bf
import numpy as np
import os, time
import joblib


load_dotenv()
marginCoin = os.environ.get('MARGIN_COIN')
symbol = os.environ.get('SYMBOL')
leverage = os.environ.get('LEVERAGE')
timeframe = os.environ.get('TIMEFRAME')
percent_trade = os.environ.get('PERCENT_TRADE')
take_proft_pcnt = os.environ.get('TAKE_PROFIT_PERCENT')
stop_loss_pcnt = os.environ.get('STOP_LOSS_PERCENT')

script_directory = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_directory, 'input your machine learning model here')
load_ML_model = joblib.load(model_path)


def open_market_order(prediction):
    # close open orders if any before opening market order
    bf.futures_cancel_open_orders(symbol)
    try:
        market_order = bf.futures_market_order(prediction, marginCoin, symbol, leverage, percent_trade, 'one_way_mode')
        market_order_msg = market_order.get('msg')

        if market_order_msg == 'success':
            time.sleep(1)
            entry_price = bf.get_futures_open_positions_info(symbol)[0].get('openPriceAvg')
            position = lambda : "LONG" if prediction == 1 else "SHORT" 
            print(f"Successfully placed {position()} position at {entry_price}.")

            # open take profit/stop loss orders
            bf.futures_SLTP_orders(symbol, marginCoin, prediction, stop_loss_pcnt, 'SL')
            bf.futures_SLTP_orders(symbol, marginCoin, prediction, take_proft_pcnt, 'TP')
        else:
            print(market_order_msg)
    except Exception as error:
        print(error)


def start_trade(event, context):
    
    np.random.seed(42)
    X_features = dp.extract_process_bitget_data(symbol, timeframe)
    predictions = load_ML_model.predict(X_features)

    prediction, prev_prediction = predictions[-1], predictions[-2]

    open_position = bf.get_futures_open_positions_info(symbol)
    is_open_position_valid = bf.is_open_position_valid(symbol)

    if not bool(open_position) and ( ( prediction != prev_prediction ) or is_open_position_valid):
        # open market order position (very first trade or after stop-loss)
        open_market_order(prediction)
    elif bool(open_position):
        if (prediction == 1 and open_position[0].get('holdSide') != 'long') or (prediction == 0 and open_position[0].get('holdSide') != 'short'):

            # close current open posion before opening new position
            PnL = float(bf.get_futures_open_positions_info(symbol)[0].get('unrealizedPL'))
            bf.futures_close_position(symbol)
            print(f"Successfully closed open position with PNL: {PnL}$.")
            
            # open market order position 
            open_market_order(prediction)
        else:
            print(f"NO ACTION: CURRENT {'LONG' if prediction == 1 else 'SHORT'} POSITION ON HOLD")
    else:
        print(f"NO OPEN POSITION: Waiting for prediction reversal >> current prediction: {prediction} vs. previous prediction: {prev_prediction} <<.")

    crypto_data = {
        "statusCode" : 200,
        "trade_info": {
            "ticker" : symbol,
            'timeframe' : timeframe,
            "prediction" : 'LONG' if prediction == 1 else 'SHORT',
            "leverage" : leverage,
            "percent_margin_trade": str(float(percent_trade) * 100) + ' %',
        }
    }   
    return crypto_data