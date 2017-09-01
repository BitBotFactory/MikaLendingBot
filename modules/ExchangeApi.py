'''
Exchange API Base class
'''

import abc
import calendar
import time


class ExchangeApi(object):
    __metaclass__ = abc.ABCMeta

    def __str__(self):
        return self.__class__.__name__.upper()

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def create_time_stamp(datestr, formatting="%Y-%m-%d %H:%M:%S"):
        return calendar.timegm(time.strptime(datestr, formatting))

    @abc.abstractmethod
    def __init__(self, cfg, log):
        '''
        Constructor
        '''

    @abc.abstractmethod
    def return_ticker(self):
        '''
        Returns the ticker for all markets.
        '''

    @abc.abstractmethod
    def return_balances(self):
        '''
        Returns available exchange balances.
        Sample output:
        {"BTC":"0.59098578","LTC":"3.31117268", ... }
        '''

    @abc.abstractmethod
    def return_available_account_balances(self, account):
        '''
        Returns balances sorted by account. You may optionally specify the
        "account" POST parameter if you wish to fetch only the balances of one
        account.

        Sample output:
        {"exchange":{"BTC":"1.19042859","BTM":"386.52379392","CHA":"0.50000000",
        "DASH":"120.00000000","STR":"3205.32958001", "VNL":"9673.22570147"},
        "margin":{"BTC":"3.90015637","DASH":"250.00238240",
        "XMR":"497.12028113"},
        "lending":{"DASH":"0.01174765","LTC":"11.99936230"}}
        '''

    @abc.abstractmethod
    def return_lending_history(self, start, stop, limit=500):
        '''
        Returns lending history within a time range specified by the "start" and
        "end" POST parameters as UNIX timestamps. "limit" may also be specified
        to limit the number of rows returned. Sample output:

        [{ "id": 175589553, "currency": "BTC", "rate": "0.00057400", "amount": "0.04374404",
         "duration": "0.47610000", "interest": "0.00001196",
         "fee": "-0.00000179", "earned": "0.00001017", "open": "2016-09-28 06:47:26",
         "close": "2016-09-28 18:13:03" }]
        '''

    @abc.abstractmethod
    def return_loan_orders(self, currency, limit=0):
        '''
        Returns the list of loan offers and demands for a given currency,
        specified by the "currency". Sample output:

        {"offers":[{"rate":"0.00200000","amount":"64.66305732","rangeMin":2,"rangeMax":8}, ... ],
         "demands":[{"rate":"0.00170000","amount":"26.54848841","rangeMin":2,"rangeMax":2}, ... ]}
        '''

    @abc.abstractmethod
    def return_open_loan_offers(self):
        '''
        Returns own open loan offers for each currency
        '''

    @abc.abstractmethod
    def return_active_loans(self):
        '''
        Returns your active loans for each currency. Sample output:

        {"provided":[{"id":75073,"currency":"LTC","rate":"0.00020000","amount":"0.72234880","range":2,
        "autoRenew":0,"date":"2015-05-10 23:45:05","fees":"0.00006000"},
        {"id":74961,"currency":"LTC","rate":"0.00002000","amount":"4.43860711","range":2,
        "autoRenew":0,"date":"2015-05-10 23:45:05","fees":"0.00006000"}],
        "used":[{"id":75238,"currency":"BTC","rate":"0.00020000","amount":"0.04843834","range":2,
        "date":"2015-05-10 23:51:12","fees":"-0.00000001"}]}
        '''

    @abc.abstractmethod
    def cancel_loan_offer(self, currency, order_number):
        '''
        Cancels a loan offer specified by the "orderNumber"
        '''

    @abc.abstractmethod
    def create_loan_offer(self, currency, amount, duration, auto_renew, lending_rate):
        '''
        Creates a loan offer for a given currency.
        '''

    @abc.abstractmethod
    def transfer_balance(self, currency, amount, from_account, to_account):
        '''
        Transfers values from one account/wallet to another
        '''


class ApiError(Exception):
    pass
