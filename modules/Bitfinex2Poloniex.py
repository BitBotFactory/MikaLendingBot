'''
Converts Bitfinex to Poloniex Api returns
'''

import datetime
import pytz


class Bitfinex2Poloniex(object):
    @staticmethod
    def convertTimestamp(timestamp):
        '''
        Converts unix timestamp
        '''
        dt = datetime.datetime.fromtimestamp(float(timestamp), pytz.utc)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def convertOpenLoanOffers(bfxOffers):
        '''
        Convert from "offers" to "returnOpenLoanOffers"
        '''
        plxOffers = {}
        for offer in bfxOffers:
            if offer['currency'] not in plxOffers:
                plxOffers[offer['currency']] = []

            if offer['direction'] == 'lend' and float(offer['remaining_amount']) > 0:
                plxOffers[offer['currency']].append({
                    "id": offer['id'],
                    "rate": str(float(offer['rate'])/36500),
                    "amount": offer['remaining_amount'],
                    "duration": offer['period'],
                    "autoRenew": 0,
                    "date": Bitfinex2Poloniex.convertTimestamp(offer['timestamp'])
                })

        return plxOffers

    @staticmethod
    def convertActiveLoans(bfxOffers):
        '''
        Convert from "credits" to "returnActiveLoans"
        '''

        plxOffers = {}
        plxOffers['provided'] = []
        plxOffers['used'] = []
        for offer in bfxOffers:
            plxOffers['provided'].append({
                "id": offer['id'],
                "currency": offer['currency'],
                "rate": str(float(offer['rate']) / 36500),
                "amount": offer['amount'],
                "duration": offer['period'],
                "autoRenew": 0,
                "date": Bitfinex2Poloniex.convertTimestamp(offer['timestamp'])
            })

        return plxOffers

    @staticmethod
    def convertLoanOrders(bfxLendbook):
        '''
        Converts from 'lendbook' to 'returnLoanOrders'
        '''

        plxOrders = {}
        plxOrders['offers'] = []
        plxOrders['demands'] = []

        for bid in bfxLendbook['bids']:
            plxOrders['demands'].append({
                'rate': '{0:0.8f}'.format(float(bid['rate']) / 36500),
                'amount': bid['amount'],
                'rangeMin': '2',
                'rangeMax': bid['period']
            })

        for ask in bfxLendbook['asks']:
            plxOrders['offers'].append({
                'rate': '{0:0.8f}'.format(float(ask['rate']) / 36500),
                'amount': ask['amount'],
                'rangeMin': '2',
                'rangeMax': ask['period']
            })

        return plxOrders

    @staticmethod
    def convertAccountBalances(bfxBalances, account=''):
        '''
        Converts from 'balances' to 'returnAvailableAccountBalances'
        '''
        balances = {}

        accountMap = {
            'trading': 'margin',
            'deposit': 'lending',
            'exchange': 'exchange'
        }

        if (account == ''):
            balances = {'margin': {}, 'lending': {}, 'exchange': {}}
        else:
            balances[account] = {}

        for balance in bfxBalances:
            if balance['type'] == 'conversion':
                continue
            if (account == '' or account == accountMap[balance['type']]) and float(balance['amount']) > 0:
                curr = balance['currency'].upper()
                balances[account][curr] = balance['available']

        return balances
