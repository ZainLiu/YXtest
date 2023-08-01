########## GEMINI 行情接口 ##########
## https://api.gemini.com/v1/pubticker/:symbol

import json
import requests

proxies = {
    "http": 'socks4://127.0.0.1:10808',
    "https": 'socks4://127.0.0.1:10808'
}
# headers = {
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
#     "cookie": "_gcl_au=1.1.367892479.1681958688; mp_d63e727b7647b63c44007c4c8876cb81_mixpanel=%7B%22distinct_id%22%3A%20%221879c8cd784a32-0d338fb5de8347-26021f51-1fa400-1879c8cd785995%22%2C%22%24device_id%22%3A%20%221879c8cd784a32-0d338fb5de8347-26021f51-1fa400-1879c8cd785995%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22New%20Public%20Site%22%3A%20true%7D"
# }
gemini_ticker = 'https://api.gemini.com/v1/pubticker/ethusd'
# gemini_ticker = 'https://www.google.com'

btc_data = requests.get(gemini_ticker,proxies=proxies).json()
# print(btc_data)
print(json.dumps(btc_data, indent=4))
