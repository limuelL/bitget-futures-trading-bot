import bitget_api_connect as api_connect
import pandas as pd
import pandas_ta as ta


def data_preprocessing(dataframe, lag):
    df_tmp = dataframe.copy()
    columns_to_keep = df_tmp.columns[5:]

    # Generate lagged features
    for i in range(lag, 0, -1):
        shifted_df_tmp = dataframe.shift(i)
        shifted_df_tmp.columns = [f"{col}_{i}" for col in dataframe.columns]
        df_tmp = pd.concat([df_tmp, shifted_df_tmp.iloc[:, 5:]], axis=1)

    df_tmp.drop(columns=columns_to_keep, inplace=True)
    df_tmp.dropna(inplace=True)
    return df_tmp


def extract_process_bitget_data(symbol, time_frame):
    request_path = '/api/v2/mix/market/candles'
    params = {'symbol': symbol,  'productType': 'USDT-FUTURES', 'granularity': time_frame, 'limit': 1000}

    candles = api_connect.bitget_request(request_path, None, params, "GET").json().get('data')
    raw_crypto = pd.DataFrame(candles, dtype='float64')
    crypto = raw_crypto.iloc[:,0:-1]

    # set columns
    crypto.columns = ["openTime", "Open", "High", "Low", "Close", "Volume"]

    # convert openTime to readable format
    pd.options.mode.copy_on_write = True
    crypto["openTime"] = pd.to_datetime(crypto["openTime"], unit='ms', utc=True)
    crypto["openTime"] = pd.to_datetime(crypto["openTime"].dt.strftime('%Y-%m-%d %H:%M:%S'))
    crypto.set_index('openTime', inplace=True)

    # add features
    crypto['smooth_close'] = ta.sma(crypto.Close, length=10)

    # add lag data
    crypto = data_preprocessing(crypto, 5)
    crypto.dropna(inplace=True)

    X_features = crypto.iloc[-2:, 5:]

    return X_features