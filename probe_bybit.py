# def calculate_final_usd(input_value, p2p_price, conversion_fee_type='spot'):
#         usdt = input_value/p2p_price
        
#         if conversion_fee_type == 'spot':
#             conversion_fee_value = 0.1
#         elif conversion_fee_type == 'auto':
#             conversion_fee_value = 0.9
            
#         usd = usdt - usdt * (conversion_fee_value/100)
#         return usd, usdt


# ---------------- payment method --------------------
# url = 'https://www.bybit.com/x-api/fiat/otc/configuration/queryAllPaymentList'
# response = requests.post(url)
# data = response.json()
# payment_configs = data['result']['paymentConfigVo']

# order_payment_ids = ['18', '40', '90', '14']

# for payment in payment_configs:
#     if payment['paymentType'] in order_payment_ids:
#         print(payment['paymentName'])



import requests
input_value = 100000


url = 'https://www.bybit.com/x-api/fiat/otc/item/online'

payload = {
    'amount': str(input_value),
    'authMaker': False,
    'bulkMaker': False,
    'canTrade': True,
    'countryCode': "",
    'currencyId': "RUB",
    'itemRegion': 1,
    'page': "1",
    'payment': [],
    'paymentPeriod': [],
    'side': "1",
    'size': "10",
    'sortStrategyCode': "DEFAULT_SELL",
    'sortType': "OVERALL_RANKING",
    'tokenId': "USDT",
    'tradeWith': False,
    'userId': "",
    'vaMaker': False,
    'verificationFilter': 0
}

payload['size'] = '500'

response = requests.post(url, json=payload)
data = response.json()

items = data['result']['items']

print(data['result']['count'])
print(len(items))