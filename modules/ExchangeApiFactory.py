'''
Factory to instanciate right API class
'''

from modules.Poloniex import Poloniex
from modules.Bitfinex import Bitfinex

EXCHANGE = {'POLONIEX': Poloniex, 'BITFINEX': Bitfinex}


class ExchangeApiFactory(object):
    @staticmethod
    def createApi(exchange, cfg):
        if exchange not in EXCHANGE:
            raise Exception("Invalid exchange: " + exchange)
        return EXCHANGE[exchange](cfg)
