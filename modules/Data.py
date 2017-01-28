import datetime
import time
from decimal import Decimal
from urllib import urlopen
import json

api = None
log = None


def init(api1, log1):
    global api, log
    api = api1
    log = log1


def get_on_order_balances():
    loan_offers = api.return_open_loan_offers()
    on_order_balances = {}
    for CUR in loan_offers:
        for offer in loan_offers[CUR]:
            on_order_balances[CUR] = on_order_balances.get(CUR, 0) + Decimal(offer['amount'])
    return on_order_balances


def get_max_duration(end_date, context):
    if not end_date:
        return ""
    try:
        now_time = datetime.date.today()
        config_date = map(int, end_date.split(','))
        end_time = datetime.date(*config_date)  # format YEAR,MONTH,DAY all ints, also used splat operator
        diff_days = (end_time - now_time).days
        if context == "order":
            return diff_days  # Order needs int
        if context == "status":
            return " - Days Remaining: " + str(diff_days)  # Status needs string
    except Exception as Ex:
        print "ERROR: There is something wrong with your endDate option. Error: " + str(Ex)
        exit(1)


def get_total_lended():
    crypto_lended = api.return_active_loans()
    total_lended = {}
    rate_lended = {}
    for item in crypto_lended["provided"]:
        item_str = item["amount"].encode("utf-8")
        item_float = Decimal(item_str)
        item_rate_str = item["rate"].encode("utf-8")
        item_rate_float = Decimal(item_rate_str)
        if item["currency"] in total_lended:
            crypto_lended_sum = total_lended[item["currency"]] + item_float
            crypto_lended_rate = rate_lended[item["currency"]] + (item_rate_float * item_float)
            total_lended[item["currency"]] = crypto_lended_sum
            rate_lended[item["currency"]] = crypto_lended_rate
        else:
            crypto_lended_sum = item_float
            crypto_lended_rate = item_rate_float * item_float
            total_lended[item["currency"]] = crypto_lended_sum
            rate_lended[item["currency"]] = crypto_lended_rate
    return [total_lended, rate_lended]


def timestamp():
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


def stringify_total_lended(total_lended, rate_lended):
    result = 'Lended: '
    for key in sorted(total_lended):
        average_lending_rate = Decimal(rate_lended[key] * 100 / total_lended[key])
        result += '[%.4f %s @ %.4f%%] ' % (Decimal(total_lended[key]), key, average_lending_rate)
        log.updateStatusValue(key, "lentSum", total_lended[key])
        log.updateStatusValue(key, "averageLendingRate", average_lending_rate)
    return result


def update_conversion_rates(output_currency, json_output_enabled):
    if json_output_enabled:
        total_lended = get_total_lended()[0]
        ticker_response = api.return_ticker()
        output_currency_found = False
        # default output currency is BTC
        if output_currency == 'BTC':
            output_currency_found = True
            log.updateOutputCurrency('highestBid', '1')
            log.updateOutputCurrency('currency', output_currency)

        for couple in ticker_response:
            currencies = couple.split('_')
            ref = currencies[0]
            currency = currencies[1]
            if ref == 'BTC' and currency in total_lended:
                log.updateStatusValue(currency, 'highestBid', ticker_response[couple]['highestBid'])
                log.updateStatusValue(currency, 'couple', couple)
            if not output_currency_found: # check for output currency
                if ref == 'BTC' and currency == output_currency:
                    output_currency_found = True
                    log.updateOutputCurrency('highestBid', 1 / float(ticker_response[couple]['highestBid']))
                    log.updateOutputCurrency('currency', output_currency)
                if ref == output_currency and currency == 'BTC':
                    output_currency_found = True
                    log.updateOutputCurrency('highestBid', ticker_response[couple]['highestBid'])
                    log.updateOutputCurrency('currency', output_currency)
        if not output_currency_found: # fetch output currency rate from blockchain.info
            url = "https://blockchain.info/tobtc?currency={0}&value=1".format(output_currency)
            try:
                highest_bid = json.loads(urlopen(url).read())
                log.updateOutputCurrency('highestBid', 1 / float(highest_bid))
                log.updateOutputCurrency('currency', output_currency)
            except ValueError:
                log.log_error("Failed to find the exchange rate for outputCurrency {0}!".format(output_currency))
                log.log_error("Make sure that {0} is either traded on Poloniex or supported by blockchain.info: {1}"\
                              .format(output_currency, "https://blockchain.info/api/exchange_rates_api"))


def get_lending_currencies():
    currencies = []
    total_lended = get_total_lended()[0]
    for cur in total_lended:
        currencies.append(cur)
    lending_balances = api.return_available_account_balances("lending")['lending']
    for cur in lending_balances:
        currencies.append(cur)
    return currencies


def truncate(f, n):
    """Truncates/pads a float f to n decimal places without rounding"""
    # From https://stackoverflow.com/questions/783897/truncating-floats-in-python
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])