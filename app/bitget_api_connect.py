from dotenv import load_dotenv
import hmac
import base64
import json
import time
import os
import requests


load_dotenv()
api_key = os.environ.get('api_key')
api_secret = os.environ.get('api_secret')
api_passphrase = os.environ.get('api_passphrase')
api_url = "https://api.bitget.com"


def parse_params_to_str(params):
    url = '?'
    for key, value in params.items():
        url = url + str(key) + '=' + str(value) + '&'

    return url[0:-1]

def get_signature(message):
    mac = hmac.new(bytes(api_secret, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    d = mac.digest()
    return base64.b64encode(d)

def bitget_request(request_path, body, query, method):
    std_time = time.time() * 1000
    new_time = int(std_time)
    if str(body) == '{}' or str(body) == 'None':
        converted_body = ''
    else:
        converted_body = json.dumps(body)

    message = str(new_time) + method + request_path + parse_params_to_str(query) + converted_body

    headers = {"ACCESS-KEY": api_key,
               "ACCESS-SIGN": get_signature(message),
               "ACCESS-TIMESTAMP": str(new_time),
               "ACCESS-PASSPHRASE": api_passphrase,
               "Content-Type": "application/json",
               "Locale": "en-PH"
               }
    
    if method == "GET":
        return requests.get((api_url + request_path), headers=headers, params=query)
    elif method == 'POST':
        return requests.post((api_url + request_path), headers=headers, data=converted_body)
    else:
        raise ValueError("Invalid HTTP method specified")