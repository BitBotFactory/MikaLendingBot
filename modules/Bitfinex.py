# coding=utf-8
import hashlib
import hmac
import base64
import json
import requests
import time

from modules.ExchangeApi import ExchangeApi
from modules.ExchangeApi import ApiError
from modules.Bitfinex2Poloniex import Bitfinex2Poloniex


class Bitfinex(ExchangeApi):
    def __init__(self, cfg):
        self.cfg = cfg
        self.url = 'https://api.bitfinex.com/v1/'
        self.key = self.cfg.get("API", "apikey", None)
        self.secret = self.cfg.get("API", "secret", None)
        self.symbols = []
        self.ticker = {}
        self.tickerTime = 0
        self.usedCurrencies = []
        self.timeout = int(self.cfg.get("BOT", "timeout", 30, 1, 180))

    @property
    def _nonce(self):
        '''
        Returns a nonce
        Used in authentication
        '''
        return str(int(round(time.time() * 1000)))

    def _sign_payload(self, payload):
        j = json.dumps(payload)
        data = base64.standard_b64encode(j.encode('utf8'))

        h = hmac.new(self.secret.encode('utf8'), data, hashlib.sha384)
        signature = h.hexdigest()
        return {
            "X-BFX-APIKEY": self.key,
            "X-BFX-SIGNATURE": signature,
            "X-BFX-PAYLOAD": data
        }

    def _request(self, request, command, payload=None, verify=True):
        try:
            r = {}
            if (request == 'get'):
                r = requests.get(self.url + command, timeout=self.timeout)
            else:
                r = requests.post(self.url + command, headers=payload, verify=verify, timeout=self.timeout)

            if r.status_code != 200:
                if (r.status_code == 502 or r.status_code in range(520, 527, 1)):
                    raise ApiError('API Error ' + str(r.status_code) +
                                   ': The web server reported a bad gateway or gateway timeout error.')
                else:
                    raise ApiError('API Error ' + str(r.status_code) + ': ' + r.text)

            return r.json()

        except Exception as ex:
            ex.message = ex.message if ex.message else str(ex)
            ex.message = "{0} Requesting {1}".format(ex.message, self.url + command)
            raise ex

    def _post(self, command, payload, verify=True):
        return self._request('post', command, payload, verify)

    def _get(self, command):
        return self._request('get', command)

    def _getSymbols(self):
        '''
        A list of symbol names. Currently "btcusd", "ltcusd", "ltcbtc", ...
        https://bitfinex.readme.io/v1/reference#rest-public-symbols
        '''
        if len(self.symbols) == 0:
            bfxResp = self._get('symbols')
            allCurrencies = self.cfg.get_all_currencies()
            for symbol in bfxResp:
                base = symbol[3:].upper()
                curr = symbol[:3].upper()
                if base in ['USD', 'BTC'] and curr in allCurrencies:
                    self.symbols.append(symbol)

        return self.symbols

    def return_open_loan_offers(self):
        '''
        Returns active loan offers
        https://bitfinex.readme.io/v1/reference#rest-auth-offers
        '''
        signed_payload = self._sign_payload({
            "request": "/v1/offers",
            "nonce": self._nonce
        })

        bfxResp = self._post("offers", signed_payload)
        resp = Bitfinex2Poloniex.convertOpenLoanOffers(bfxResp)

        return resp

    def return_loan_orders(self, currency, limit=0):
        command = ('lendbook/' + currency + '?limit_asks=' + str(limit) + '&limit_bids=' + str(limit))
        bfxResp = self._get(command)
        resp = Bitfinex2Poloniex.convertLoanOrders(bfxResp)

        return resp

    def return_active_loans(self):
        '''
        Returns own active loan offers
        https://bitfinex.readme.io/v1/reference#rest-auth-offers
        '''
        signed_payload = self._sign_payload({
            "request": "/v1/credits",
            "nonce": self._nonce
        })

        bfxResp = self._post("credits", signed_payload)
        resp = Bitfinex2Poloniex.convertActiveLoans(bfxResp)

        return resp

    def return_ticker(self):
        '''
        The ticker is a high level overview of the state of the market
        https://bitfinex.readme.io/v1/reference#rest-public-ticker
        '''
        t = int(time.time())
        if (t - self.tickerTime < 60):
            return self.ticker

        for symbol in self._getSymbols():
            base = symbol[3:].upper()
            curr = symbol[:3].upper()
            if base in ['BTC', 'USD'] and (curr == 'BTC' or curr in self.usedCurrencies):
                couple = (base + '_' + curr)
                coupleReverse = (curr + '_' + base)

                try:
                    ticker = self._get('pubticker/'+symbol)
                except ApiError as e:
                    if not self.ticker[couple]:
                        raise e

                if 'message' in ticker:
                    raise ApiError("Error: %s (%s)".format(ticker['message'], symbol))

                self.ticker[couple] = {
                    "last": ticker['last_price'],
                    "lowestAsk": ticker['ask'],
                    "highestBid": ticker['bid'],
                    "percentChange": "",
                    "baseVolume": str(float(ticker['volume'])*float(ticker['mid'])),
                    "quoteVolume": ticker['volume']
                }
                self.ticker[coupleReverse] = {
                    "last": 1 / float(self.ticker[couple]['last']),
                    "lowestAsk": 1 / float(self.ticker[couple]['lowestAsk']),
                    "highestBid": 1 / float(self.ticker[couple]['highestBid'])
                }

        self.tickerTime = t

        return self.ticker

    def return_available_account_balances(self, account):
        '''
        Returns own balances sorted by account
        https://bitfinex.readme.io/v1/reference#rest-auth-wallet-balances
        '''
        signed_payload = self._sign_payload({
            "request": "/v1/balances",
            "nonce": self._nonce
        })

        bfxResp = self._post("balances", signed_payload)
        filtered_response = [x for x in bfxResp if x['type'] != 'conversion']
        balances = Bitfinex2Poloniex.convertAccountBalances(filtered_response, account)

        if 'lending' in balances:
            self.usedCurrencies = []
            for curr in balances['lending']:
                self.usedCurrencies.append(curr)

        return balances

    def cancel_loan_offer(self, currency, order_number):
        '''
        Cancels an offer
        https://bitfinex.readme.io/v1/reference#rest-auth-cancel-offer
        '''
        signed_payload = self._sign_payload({
            "request": "/v1/offer/cancel",
            "offer_id": order_number,
            "nonce": self._nonce
        })

        bfxResp = self._post("offer/cancel", signed_payload)

        success = 0
        message = ''
        try:
            if bfxResp['id'] == order_number:
                success = 1
                message = "Loan offer canceled ({:.4f} @ {:.4f}%).".format(float(bfxResp['remaining_amount']),
                                                                           float(bfxResp['rate'])/365)
        except Exception as e:
            message = "Error canceling offer: ", str(e)
            success = 0

        return {"success": success, "message": message}

    def create_loan_offer(self, currency, amount, duration, auto_renew, lending_rate):
        '''
        Creates a loan offer for a given currency.
        https://bitfinex.readme.io/v1/reference#rest-auth-new-offer
        '''

        signed_payload = self._sign_payload({
            "request": "/v1/offer/new",
            "currency": currency,
            "amount": str(amount),
            "rate": str(lending_rate * 36500),
            "period": int(duration),
            "direction": "lend",
            "nonce": self._nonce
        })

        try:
            bfxResp = self._post("offer/new", signed_payload)
            plxResp = {"success": 0, "message": "Error", "orderID": 0}
            if bfxResp['id']:
                plxResp['orderId'] = bfxResp['id']
                plxResp['success'] = 1
                plxResp['message'] = "Loan order placed."
            return plxResp

        except Exception as e:
                msg = str(e)
                # "Invalid offer: incorrect amount, minimum is 50 dollar or equivalent in USD"
                if "Invalid offer: incorrect amount, minimum is 50" in msg:
                    usd_min = 50
                    cur_min = usd_min
                    if currency != 'USD':
                        cur_min = usd_min / float(self.return_ticker()['USD_'+currency]['lowestAsk'])

                    raise Exception("Error create_loan_offer: Amount must be at least " + str(cur_min) + " " + currency)
                else:
                    raise e

    def return_balances(self):
        '''
        Returns balances of exchange wallet
        https://bitfinex.readme.io/v1/reference#rest-auth-wallet-balances
        '''
        balances = self.return_available_account_balances('exchange')
        return balances['exchange']

    def transfer_balance(self, currency, amount, from_account, to_account):
        '''
        Transfers values from one account/wallet to another
        https://bitfinex.readme.io/v1/reference#rest-auth-transfer-between-wallets
        '''
        accountMap = {
            'margin': 'trading',
            'lending': 'deposit',
            'exchange': 'exchange'
        }
        signed_payload = self._sign_payload({
            "request": "/v1/transfer",
            "currency": currency,
            "amount": amount,
            "walletfrom": accountMap[from_account],
            "walletto": accountMap[to_account],
            "nonce": self._nonce
        })

        bfxResp = self._post("transfer", signed_payload)
        plxResp = {
            "status":  1 if bfxResp[0]['status'] == "success" else 0,
            "message": bfxResp[0]['message']
        }

        return plxResp

    def return_lending_history(self, start, stop, limit=500):
        '''
        Retrieves balance ledger entries. Search funding payments in it and returns
        it as history.
        https://bitfinex.readme.io/v1/reference#rest-auth-balance-history
        '''
        history = []
        allCurrencies = self.cfg.get_all_currencies()
        for curr in allCurrencies:
            signed_payload = self._sign_payload({
                "request": "/v1/history",
                "currency": curr,
                "since": str(start),
                "until": str(stop),
                "limit": limit,
                "wallet": "deposit",
                "nonce": self._nonce
            })
            bfxResp = self._post('history', signed_payload)
            for entry in bfxResp:
                if 'Margin Funding Payment' in entry['description']:
                    amount = float(entry['amount'])
                    history.append({
                        "id": int(float(entry['timestamp'])),
                        "currency": curr,
                        "rate": "0.0",
                        "amount": "0.0",
                        "duration": "0.0",
                        "interest": str(amount/0.85),
                        "fee": str(amount-amount/0.85),
                        "earned": str(amount),
                        "open": Bitfinex2Poloniex.convertTimestamp(entry['timestamp']),
                        "close": Bitfinex2Poloniex.convertTimestamp(entry['timestamp'])
                    })

        return history
