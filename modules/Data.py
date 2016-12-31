import datetime
import time
from decimal import Decimal

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
        for couple in ticker_response:
            currencies = couple.split('_')
            ref = currencies[0]
            currency = currencies[1]
            if ref == 'BTC' and currency in total_lended:
                log.updateStatusValue(currency, 'highestBid', ticker_response[couple]['highestBid'])
                log.updateStatusValue(currency, 'couple', couple)
            if output_currency == 'USDT' and ref == 'USDT' and currency == 'BTC':
                log.updateOutputCurrency('highestBid', ticker_response[couple]['highestBid'])
                log.updateOutputCurrency('currency', output_currency)
            if output_currency != 'USDT' and ref == 'BTC' and currency == output_currency:
                log.updateOutputCurrency('highestBid', ticker_response[couple]['highestBid'])
                log.updateOutputCurrency('currency', output_currency)
        if output_currency == 'BTC':
            log.updateOutputCurrency('highestBid', '1')
            log.updateOutputCurrency('currency', output_currency)


def get_lending_currencies():
    currencies = []
    total_lended = get_total_lended()[0]
    for cur in total_lended:
        currencies.append(cur)
    lending_balances = api.return_available_account_balances("lending")['lending']
    for cur in lending_balances:
        currencies.append(cur)
    return currencies
