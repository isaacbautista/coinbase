# python libraries
import requests
import json
import hmac
import hashlib
import base64
import time
import datetime
from os import getenv
from requests.auth import AuthBase
from operator import itemgetter

class CoinbaseAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        message = ''.join([timestamp, request.method,
                           request.path_url, (request.body or '')])
        request.headers.update(self.get_auth_headers(timestamp, message,
                                                self.api_key,
                                                self.secret_key,
                                                self.passphrase))
        return request


    def get_auth_headers(self, timestamp, message, api_key, secret_key, passphrase):
        message = message.encode('ascii')
        hmac_key = base64.b64decode(secret_key)
        signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest()).decode('utf-8')
        return {
            'Content-Type': 'application/json',
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': api_key,
            'CB-ACCESS-PASSPHRASE': passphrase
            }

class CoinbasePublic():
    def __init__(self, sandbox=False):
        if sandbox:
            self.url = " https://api-public.sandbox.pro.coinbase.com"
        else:
            self.url   = "https://api.pro.coinbase.com"

    def parse_orders(self, orders):
        # list of lists
        # objective: list of lists [[price, amount]]
        aggregate = []
        for order in orders:
            aggregate.append(["Coinbase Pro", order[0], order[1]])
        return aggregate

    def get_orderbook(self, pair="BTC-USD", level=2):
        """
        pair: <string> currency pair - default: BTC-USD
        level: <int> response detail - default: 2
        returns: <dict>
        """
        response = requests.get(self.url+"/products/"+pair+"/book", params={"level":level})

        orderbook = response.json()
        return orderbook

    def get_bids(self, pair="BTC-USD", level=2):
        """
        pair: <string> currency pair - default: BTC-USD
        level: <int> response detail - default: 2
        returns: <list> [ price, size, num-orders ]
        """
        bids = self.get_orderbook(pair, level)["bids"]
        return self.parse_orders(bids)

    def get_asks(self, pair="BTC-USD", level=2):
        """
        pair: <string> currency pair - default: BTC-USD
        level: <int> response detail - default: 2
        returns: <list> [ price, size, num-orders ]
        """
        asks = self.get_orderbook(pair, level)["asks"]
        return self.parse_orders(asks)

    def get_history(self, pair="BTC-USD", start_day=None, end_day=None, interval="1d", limit=300):

        intervals = {
            "1m": "60",
            "5m": "300",
            "15m": "900",
            "1h": "3600",
            "6h": "12600",
            "1d": "86400"
        }

        if interval not in intervals.keys():
            return 0

        params = {
            # "start": ,
            # "end": ,
            "granularity": intervals[interval]
        }

        if start_day is None and end_day is None:
            # default: 30 days back
            startTime = int(time.time() - 3600*24*30)
            endTime = int(time.time())

        if start_day is None and end_day is not None:
            # if only end_day is specified, go back 30 days from that
            endTime = int(time.mktime(time.strptime(end_day, "%m/%d/%y")))
            startTime = endTime - 3600*24*30

        if start_day is not None and end_day is None:
            # if only start day is speficied, go forward 30 days after that
            startTime = int(time.mktime(time.strptime(start_day, "%m/%d/%y")))
            endTime = startTime + 3600*24*30

        if start_day is not None and end_day is not None:
            # if both start_day and end_day are specified
            startTime = int(time.mktime(time.strptime(start_day, "%m/%d/%y")))
            endTime = int(time.mktime(time.strptime(end_day, "%m/%d/%y")))

        if interval == "1m":
            divisor = 60*1
        elif interval == "5m":
            divisor = 60*5
        elif interval == "15m":
            divisor = 60*5
        elif interval == "1h":
            divisor = 3600
        elif interval == "6h":
            divisor = 3600*6
        elif interval == "1d":
            divisor = 3600*24
        else:
            return 0

        divisor = divisor * limit

        # need to add +1 for edge case when int floors to 0
        intervals = int((endTime - startTime) / divisor + 1)

        # amount of time in each interval
        diff = int((endTime - startTime) / intervals)

        runningTime = startTime + diff

        response = []

        breakout = False

        while(runningTime <= endTime):
            params["start"] = datetime.datetime.fromtimestamp(startTime, tz=datetime.timezone.utc).isoformat()
            params["end"] = datetime.datetime.fromtimestamp(runningTime, tz=datetime.timezone.utc).isoformat()


            # let's not troll the API
            time.sleep(1)
            r = requests.get(self.url+"/products/"+pair+"/candles", params)
            # self.check_response(r)
            r = r.json()
            for data in r:
                response.append(data)
            startTime += diff
            runningTime += diff


            if breakout:
                break

            if runningTime > endTime:
                runningTime = endTime
                breakout = True

        response = sorted(response, key=itemgetter(0))

        for row in response:
            row.insert(1, int(row[0] + divisor/limit - 1))

        return response

    def print_history(self, history):
        for row in history:
            print(f"{row[0]} \t {row[1]} \t {row[4]}")

    def save_historical_data(self, data, filename):
        # save historical data in .csv file
        # open time, close time, open, high, low, close, volume
        f = open(filename, "w")
        for row in data:
            # open_time = str(time.ctime(row[0]/1000))
            # close_time = str(time.ctime(row[6]/1000))
            open_time = str(int(row[0]))
            close_time = str(int(row[1]))
            low = str(row[2])
            high = str(row[3])
            open_price = str(row[4])
            close = str(row[5])
            volume = str(row[6])
            f.write(open_time)
            f.write(",")
            f.write(close_time)
            f.write(",")
            f.write(open_price)
            f.write(",")
            f.write(high)
            f.write(",")
            f.write(low)
            f.write(",")
            f.write(close)
            f.write(",")
            f.write(volume)
            f.write("\n")
        f.close()

class CoinbasePrivate(CoinbasePublic):
    def __init__(self, sandbox=False):
        if sandbox:
            self.url = " https://api-public.sandbox.pro.coinbase.com"
            self.private_key = getenv("Coinbase_KEY_SANDBOX")
            self.public_key  = getenv("Coinbase_KEY_PUBLIC_SANDBOX")
            self.passphrase = getenv("Coinbase_PASSPHRASE_SANDBOX")
        else:
            self.url   = "https://api.pro.coinbase.com"
            self.private_key = getenv("Coinbase_KEY")
            self.public_key  = getenv("Coinbase_KEY_PUBLIC")
            self.passphrase = getenv("Coinbase_PASSPHRASE")

        # super().__init__()
        self.auth = CoinbaseAuth(self.public_key, self.private_key, self.passphrase)

    def get_accounts(self):
        r = requests.get(self.url + "/accounts/", auth=self.auth)
        return r.json()

    def print_accounts(self):
        accounts = self.get_accounts()
        print("{:5} \t {:10}".format("Currency", "Amount"))
        for account in accounts:
            print("{:5} \t {:10}".format(account["currency"], account["balance"]))

    def get_products(self):
        r = requests.get(self.url+"/products/")
        return r.json()

    def place_order(self, size, price, side, symbol="BTC-USD", order_type="limit", time_in_force="GTC"):
        params = {"size": size,
                  "price": price,
                  "side": side,
                  "product_id": symbol,
                  "type": order_type,
                  "post_only": "false",
                  "time_in_force": time_in_force
                  }
        if time_in_force == "GTT":
            params["cancel_after"] = "min"
        r = requests.post(self.url + "/orders/", auth=self.auth, data=json.dumps(params))

        # error handling for insufficient funds
        if r.json() == {"message": "Insufficient funds"}:
            print("Error: Insufficient funds")
            return 0
        if r.json() == {"message": "size is too large. Maximum size is 10000"}:
            print("Error: Order size too large. Maximum size is 10000")
            return 0

        return r.json()

    def limit_buy(self, size, price, symbol="BTC-USD", time_in_force="GTC"):
        return self.place_order(size, price, "buy", symbol, order_type="limit", time_in_force=time_in_force)

    def limit_sell(self, size, price, symbol="BTC-USD", time_in_force="GTC"):
        return self.place_order(size, price, "sell", symbol, order_type="limit", time_in_force=time_in_force)

    def cancel_order(self, order_id):
        r = requests.delete(self.url + "/orders/" + order_id, auth=self.auth)
        return r.json()

    def cancel_all_orders(self):
        r = requests.delete(self.url + "/orders", auth=self.auth)
        return r.json()

    def get_orders(self):
        r = requests.get(self.url+"/orders?status=all", auth=self.auth)
        return r.json()

    def print_orders(self):
        orders = self.get_orders()
        print("=========Coinbase Pro=========")
        print("{:7} \t {:5} \t {:^10} \t {:5} \t {:5} \t {:^18}".format("Product", "Size", "Price USD", "Type", "Side", "Time"))
        print()
        for order in orders:
            print("{:7} \t {:.3f} \t {:9.2f} \t {:5} \t {:5} \t {:10} {:8} \t {:8}".format(
            order["product_id"],
            float(order["size"]),
            float(order["price"]),
            order["type"],
            order["side"],
            order["created_at"][:10],
            order["created_at"][11:19],
            order["status"]))

    def immediate_buy(self, size, price, symbol="BTC-USD"):
        return self.place_order(size, price, "buy", symbol, order_type="limit", time_in_force="IOC")

    def immediate_sell(self, size, price, symbol="BTC-USD"):
        return self.place_order(size, price, "sell", symbol, order_type="limit", time_in_force="IOC")
