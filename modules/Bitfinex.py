# coding=utf-8
import hashlib
import hmac
import base64
import json
import requests
import time
import threading

from modules.ExchangeApi import ExchangeApi
from modules.ExchangeApi import ApiError
from modules.Bitfinex2Poloniex import Bitfinex2Poloniex
from modules.RingBuffer import RingBuffer


class Bitfinex(ExchangeApi):
    def __init__(self, cfg, log):
        super(Bitfinex, self).__init__(cfg, log)
        self.cfg = cfg
        self.log = log
        self.lock = threading.RLock()
        self.req_per_period = 1
        self.default_req_period = 1000  # milliseconds, 1000 = 60/min
        self.req_period = self.default_req_period
        self.req_time_log = RingBuffer(self.req_per_period)
        self.url = 'https://api.bitfinex.com'
        self.key = self.cfg.get("API", "apikey", None)
        self.secret = self.cfg.get("API", "secret", None)
        self.apiVersion = 'v1'
        self.symbols = []
        self.ticker = {}
        self.tickerTime = 0
	self.baseCurrencies = ['USD', 'BTC', 'ETH']
        self.all_currencies = self.cfg.get_all_currencies()
        self.usedCurrencies = []
        self.timeout = int(self.cfg.get("BOT", "timeout", 30, 1, 180))
        self.api_debug_log = self.cfg.getboolean("BOT", "api_debug_log")
        # Initialize usedCurrencies
        _ = self.return_available_account_balances("lending")

    @property
    def _nonce(self):
        """
        Returns a nonce
        Used in authentication
        """
        return str(int(time.time() * 100000))

    def limit_request_rate(self):
        super(Bitfinex, self).limit_request_rate()

    def increase_request_timer(self):
        super(Bitfinex, self).increase_request_timer()

    def decrease_request_timer(self):
        super(Bitfinex, self).decrease_request_timer()

    def reset_request_timer(self):
        super(Bitfinex, self).reset_request_timer()

    def _sign_payload(self, payload):
        j = json.dumps(payload)
        data = base64.standard_b64encode(j.encode('utf8'))

        h = hmac.new(self.secret.encode('utf8'), data, hashlib.sha384)
        signature = h.hexdigest()
        return {
            "X-BFX-APIKEY": self.key,
            "X-BFX-SIGNATURE": signature,
            "X-BFX-PAYLOAD": data,
            "Connection": "close"
        }

    def _request(self, method, request, payload=None, verify=True):
        try:

            r = {}
            url = '{}{}'.format(self.url, request)
            if method == 'get':
                r = requests.get(url, timeout=self.timeout, headers={'Connection': 'close'})
            else:
                r = requests.post(url, headers=payload, verify=verify, timeout=self.timeout)

            if r.status_code != 200:
                if r.status_code == 502 or r.status_code in range(520, 527, 1):
                    raise ApiError('API Error ' + str(r.status_code) +
                                   ': The web server reported a bad gateway or gateway timeout error.')
                elif r.status_code == 429:
                    self.increase_request_timer()
                raise ApiError('API Error ' + str(r.status_code) + ': ' + r.text)

            # Check in case something has gone wrong and the timer is too big
            self.reset_request_timer()
            return r.json()

        except Exception as ex:
            ex.message = ex.message if ex.message else str(ex)
            ex.message = "{0} Requesting {1}".format(ex.message, self.url + request)
            raise ex

    @ExchangeApi.synchronized
    def _post(self, command, payload=None, verify=True):
        # keep the request per minute limit
        self.limit_request_rate()

        payload = payload or {}
        payload['request'] = '/{}/{}'.format(self.apiVersion, command)
        payload['nonce'] = self._nonce
        signed_payload = self._sign_payload(payload)
        return self._request('post', payload['request'], signed_payload, verify)

    @ExchangeApi.synchronized
    def _get(self, command):
        # keep the request per minute limit
        self.limit_request_rate()

        request = '/{}/{}'.format(self.apiVersion, command)
        return self._request('get', request)

    def _get_symbols(self):
        """
        A list of symbol names. Currently "btcusd", "ltcusd", "ltcbtc", ...
        https://bitfinex.readme.io/v1/reference#rest-public-symbols
        """
        if len(self.symbols) == 0:
            bfx_resp = self._get('symbols')
            for symbol in bfx_resp:
                base = symbol[3:].upper()
                curr = symbol[:3].upper()
                if ( base in self.baseCurrencies ) and ( curr in self.all_currencies ):
                    self.symbols.append(symbol)

        return self.symbols

    def return_open_loan_offers(self):
        """
        Returns active loan offers
        https://bitfinex.readme.io/v1/reference#rest-auth-offers
        """
        bfx_resp = self._post('offers')
        resp = Bitfinex2Poloniex.convertOpenLoanOffers(bfx_resp)

        return resp

    def return_loan_orders(self, currency, limit=0):
        command = ('lendbook/' + currency + '?limit_asks=' + str(limit) + '&limit_bids=' + str(limit))
        bfx_resp = self._get(command)
        resp = Bitfinex2Poloniex.convertLoanOrders(bfx_resp)

        return resp

    def return_active_loans(self):
        """
        Returns own active loan offers
        https://bitfinex.readme.io/v1/reference#rest-auth-offers
        """
        bfx_resp = self._post('credits')
        resp = Bitfinex2Poloniex.convertActiveLoans(bfx_resp)

        return resp

    def return_ticker(self):
        """
        The ticker is a high level overview of the state of the market
        https://bitfinex.readme.io/v1/reference#rest-public-ticker
        """
        t = int(time.time())
        if t - self.tickerTime < 60:
            return self.ticker

        set_ticker_time = True

        for symbol in self._get_symbols():
            base = symbol[3:].upper()
            curr = symbol[:3].upper()
            if ( base in self.baseCurrencies ) and (curr == 'BTC' or curr in self.usedCurrencies):
                couple = (base + '_' + curr)
                couple_reverse = (curr + '_' + base)

                try:
                    ticker = self._get('pubticker/' + symbol)

                    if 'message' in ticker:
                        raise ApiError("Error: {} ({})".format(ticker['message'], symbol))

                    self.ticker[couple] = {
                        "last": ticker['last_price'],
                        "lowestAsk": ticker['ask'],
                        "highestBid": ticker['bid'],
                        "percentChange": "",
                        "baseVolume": str(float(ticker['volume']) * float(ticker['mid'])),
                        "quoteVolume": ticker['volume']
                    }
                    self.ticker[couple_reverse] = {
                        "last": 1 / float(self.ticker[couple]['last']),
                        "lowestAsk": 1 / float(self.ticker[couple]['lowestAsk']),
                        "highestBid": 1 / float(self.ticker[couple]['highestBid'])
                    }

                except Exception as ex:
                    self.log.log_error('Error retrieving ticker for {}: {}. Continue with next currency.'
                                       .format(symbol, ex.message))
                    set_ticker_time = False
                    continue

        if set_ticker_time and len(self.ticker) > 2:  # USD_BTC and BTC_USD are always in
            self.tickerTime = t

        return self.ticker

    def return_available_account_balances(self, account):
        """
        Returns own balances sorted by account
        https://bitfinex.readme.io/v1/reference#rest-auth-wallet-balances
        """
        bfx_resp = self._post('balances')
        balances = Bitfinex2Poloniex.convertAccountBalances(bfx_resp, account)

        if 'lending' in balances:
            for curr in balances['lending']:
                if curr not in self.usedCurrencies:
                    self.usedCurrencies.append(curr)

        return balances

    def cancel_loan_offer(self, currency, order_number):
        """
        Cancels an offer
        https://bitfinex.readme.io/v1/reference#rest-auth-cancel-offer
        """
        payload = {
            "offer_id": order_number,
        }

        bfx_resp = self._post('offer/cancel', payload)

        success = 0
        message = ''
        try:
            if bfx_resp['id'] == order_number:
                success = 1
                message = "Loan offer canceled ({:.4f} @ {:.4f}%).".format(float(bfx_resp['remaining_amount']),
                                                                           float(bfx_resp['rate']) / 365)
        except Exception as e:
            message = "Error canceling offer: ", str(e)
            success = 0

        return {"success": success, "message": message}

    def create_loan_offer(self, currency, amount, duration, auto_renew, lending_rate):
        """
        Creates a loan offer for a given currency.
        https://bitfinex.readme.io/v1/reference#rest-auth-new-offer
        """

        payload = {
            "currency": currency,
            "amount": str(amount),
            "rate": str(round(float(lending_rate), 10) * 36500),
            "period": int(duration),
            "direction": "lend"
        }

        try:
            bfx_resp = self._post('offer/new', payload)
            plx_resp = {"success": 0, "message": "Error", "orderID": 0}
            if bfx_resp['id']:
                plx_resp['orderId'] = bfx_resp['id']
                plx_resp['success'] = 1
                plx_resp['message'] = "Loan order placed."
            return plx_resp

        except Exception as e:
                msg = str(e)
                # "Invalid offer: incorrect amount, minimum is 50 dollar or equivalent in USD"
                if "Invalid offer: incorrect amount, minimum is 50" in msg:
                    usd_min = 50
                    cur_min = usd_min
                    if currency != 'USD':
                        cur_min = usd_min / float(self.return_ticker()['USD_' + currency]['lowestAsk'])

                    raise Exception("Error create_loan_offer: Amount must be at least " + str(cur_min) + " " + currency)
                else:
                    raise e

    def return_balances(self):
        """
        Returns balances of exchange wallet
        https://bitfinex.readme.io/v1/reference#rest-auth-wallet-balances
        """
        balances = self.return_available_account_balances('exchange')
        return_dict = {cur: u'0.00000000' for cur in self.cfg.get_all_currencies()}
        return_dict.update(balances['exchange'])
        return return_dict

    def transfer_balance(self, currency, amount, from_account, to_account):
        """
        Transfers values from one account/wallet to another
        https://bitfinex.readme.io/v1/reference#rest-auth-transfer-between-wallets
        """
        account_map = {
            'margin': 'trading',
            'lending': 'deposit',
            'exchange': 'exchange'
        }
        payload = {
            "currency": currency,
            "amount": amount,
            "walletfrom": account_map[from_account],
            "walletto": account_map[to_account]
        }

        bfx_resp = self._post('transfer', payload)
        plx_resp = {
            "status":  1 if bfx_resp[0]['status'] == "success" else 0,
            "message": bfx_resp[0]['message']
        }

        return plx_resp

    def return_lending_history(self, start, stop, limit=500):
        """
        Retrieves balance ledger entries. Search funding payments in it and returns
        it as history.
        https://bitfinex.readme.io/v1/reference#rest-auth-balance-history
        """
        history = []
        all_currencies = self.cfg.get_all_currencies()
        for curr in all_currencies:
            payload = {
                "currency": curr,
                "since": str(start),
                "until": str(stop),
                "limit": limit,
                "wallet": "deposit"
            }
            bfx_resp = self._post('history', payload)
            for entry in bfx_resp:
                if 'Margin Funding Payment' in entry['description']:
                    amount = float(entry['amount'])
                    history.append({
                        "id": int(float(entry['timestamp'])),
                        "currency": curr,
                        "rate": "0.0",
                        "amount": "0.0",
                        "duration": "0.0",
                        "interest": str(amount / 0.85),
                        "fee": str(amount - amount / 0.85),
                        "earned": str(amount),
                        "open": Bitfinex2Poloniex.convertTimestamp(entry['timestamp']),
                        "close": Bitfinex2Poloniex.convertTimestamp(entry['timestamp'])
                    })

        return history
