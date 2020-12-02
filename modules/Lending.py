# coding=utf-8
from decimal import Decimal
import sched
import time
import threading
Config = None
api = None
log = None
Data = None
MaxToLend = None
Analysis = None

SATOSHI = Decimal(10) ** -8

sleep_time_active = 0
sleep_time_inactive = 0
sleep_time = 0
min_daily_rate = 0
max_daily_rate = 0
spread_lend = 0
gap_bottom_default = 0
gap_top_default = 0
xday_threshold = 0
xday_spread = 0
xdays = 0
min_loan_size = 0
min_loan_sizes = {}
end_date = None
coin_cfg = {}
dry_run = 0
transferable_currencies = []
currencies_to_analyse = []
keep_stuck_orders = True
hide_coins = True
coin_cfg_alerted = {}
max_active_alerted = {}
notify_conf = {}
loans_provided = {}
gap_mode_default = ""
scheduler = None
exchange = None
frrasmin = False
frrdelta = 0.0

# limit of orders to request
loanOrdersRequestLimit = {}
defaultLoanOrdersRequestLimit = 100


def init(cfg, api1, log1, data, maxtolend, dry_run1, analysis, notify_conf1):
    global Config, api, log, Data, MaxToLend, Analysis, notify_conf
    Config = cfg
    api = api1
    log = log1
    Data = data
    MaxToLend = maxtolend
    Analysis = analysis
    notify_conf = notify_conf1

    global sleep_time, sleep_time_active, sleep_time_inactive, min_daily_rate, max_daily_rate, spread_lend, \
        gap_bottom_default, gap_top_default, xday_threshold, xday_spread, xdays, min_loan_size, end_date, coin_cfg, \
        min_loan_sizes, dry_run, transferable_currencies, keep_stuck_orders, hide_coins, scheduler, gap_mode_default, \
        exchange, analysis_method, currencies_to_analyse, all_currencies, frrasmin, frrdelta

    exchange = Config.get_exchange()

    sleep_time_active = float(Config.get("BOT", "sleeptimeactive", None, 1, 3600))
    sleep_time_inactive = float(Config.get("BOT", "sleeptimeinactive", None, 1, 3600))
    exchangeMax = 7 if exchange == 'BITFINEX' else 5
    min_daily_rate = Decimal(Config.get("BOT", "mindailyrate", None, 0.003, exchangeMax)) / 100
    max_daily_rate = Decimal(Config.get("BOT", "maxdailyrate", None, 0.003, exchangeMax)) / 100
    spread_lend = int(Config.get("BOT", "spreadlend", None, 1, 20))
    gap_mode_default = Config.get_gap_mode("BOT", "gapMode")
    gap_bottom_default = Decimal(Config.get("BOT", "gapbottom", None, 0))
    gap_top_default = Decimal(Config.get("BOT", "gaptop", None, gap_bottom_default))
    xday_threshold = float(Config.get("BOT", "xdaythreshold", None, 0.003, 5)) / 100
    xday_spread = float(Config.get('BOT', 'xdayspread', 0, 0, 10))
    maxPeriod = 120 if exchange == 'BITFINEX' else 60
    xdays = str(Config.get("BOT", "xdays", None, 2, maxPeriod))
    min_loan_size = Decimal(Config.get("BOT", 'minloansize', None, 0.01))
    end_date = Config.get('BOT', 'endDate')
    coin_cfg = Config.get_coin_cfg()
    min_loan_sizes = Config.get_min_loan_sizes()
    dry_run = dry_run1
    transferable_currencies = Config.get_currencies_list('transferableCurrencies')
    all_currencies = Config.get_all_currencies()
    currencies_to_analyse = Config.get_currencies_list('analyseCurrencies', 'MarketAnalysis')
    keep_stuck_orders = Config.getboolean('BOT', "keepstuckorders", True)
    hide_coins = Config.getboolean('BOT', 'hideCoins', True)
    frrasmin = Config.getboolean('BOT', 'frrasmin', False)
    frrdelta = Decimal(Config.get('BOT', 'frrdelta', 0.0000))
    analysis_method = Config.get('Daily_min', 'method', 'percentile')
    if analysis_method not in ['percentile', 'MACD']:
        raise ValueError("analysis_method: \"{0}\" is not valid, must be percentile or MACD".format(analysis_method))

    sleep_time = sleep_time_active  # Start with active mode

    # create the scheduler thread
    scheduler = sched.scheduler(time.time, time.sleep)
    if notify_conf['notify_summary_minutes']:
        # Wait 10 seconds before firing the first summary notifcation, then use the config time value for future updates
        scheduler.enter(10, 1, notify_summary, (notify_conf['notify_summary_minutes'] * 60, ))
    if notify_conf['notify_new_loans']:
        scheduler.enter(20, 1, notify_new_loans, (60, ))
    if not scheduler.empty():
        t = threading.Thread(target=scheduler.run)
        t.start()


def get_sleep_time():
    return sleep_time


def set_sleep_time(usable):
    global sleep_time
    if usable == 0:  # After loop, if no currencies had enough to lend, use inactive sleep time.
        sleep_time = sleep_time_inactive
    else:  # Else, use active sleep time.
        sleep_time = sleep_time_active


def notify_summary(sleep_time):
    try:
        log.notify(Data.stringify_total_lent(*Data.get_total_lent()), notify_conf)
    except Exception as ex:
        ex.message = ex.message if ex.message else str(ex)
        print("Error during summary notification: {0}".format(ex.message))
    scheduler.enter(sleep_time, 1, notify_summary, (sleep_time, ))


def notify_new_loans(sleep_time):
    global loans_provided
    try:
        new_provided = api.return_active_loans()['provided']
        if loans_provided:
            # function to return a set of ids from the api result
            # get_id_set = lambda loans: set([x['id'] for x in loans])
            def get_id_set(loans):
                return set([x['id'] for x in loans])
            loans_amount = {}
            loans_info = {}
            for loan_id in get_id_set(new_provided) - get_id_set(loans_provided):
                loan = [x for x in new_provided if x['id'] == loan_id][0]
                # combine loans with the same rate
                k = 'c' + loan['currency'] + 'r' + loan['rate'] + 'd' + str(loan['duration'])
                loans_amount[k] = float(loan['amount']) + (loans_amount[k] if k in loans_amount else 0)
                loans_info[k] = loan
            # send notifications with the grouped info
            for k, amount in loans_amount.iteritems():
                loan = loans_info[k]
                t = "{0} {1} loan filled for {2} days at a rate of {3:.4f}%"
                text = t.format(amount, loan['currency'], loan['duration'], float(loan['rate']) * 100)
                log.notify(text, notify_conf)
        loans_provided = new_provided
    except Exception as ex:
        ex.message = ex.message if ex.message else str(ex)
        print("Error during new loans notification: {0}".format(ex.message))
    scheduler.enter(sleep_time, 1, notify_new_loans, (sleep_time, ))


def get_min_loan_size(currency):
    if currency not in min_loan_sizes:
        return min_loan_size
    return Decimal(min_loan_sizes[currency])


def create_lend_offer(currency, amt, rate):
    days = '2'
    if float(rate) > 0.0001:
        rate = float(rate) - 0.000001  # lend offer just bellow the competing one
    amt = "%.8f" % Decimal(amt)
    if xday_threshold > 0:
        if float(rate) >= xday_threshold:
            days = xdays
        elif xday_spread and xday_spread > 0:
            xday_threshold_min = xday_threshold / xday_spread
            if float(rate) > xday_threshold_min:
                m = (float(xdays) - 2) / (xday_threshold - xday_threshold_min)
                days = str(int(round(m * (float(rate) - xday_threshold_min) + 2)))
    if Config.has_option('BOT', 'endDate'):
        days_remaining = int(Data.get_max_duration(end_date, "order"))
        if int(days_remaining) <= 2:
            print "endDate reached. Bot can no longer lend.\nExiting..."
            log.log("The end date has almost been reached and the bot can no longer lend. Exiting.")
            log.refreshStatus(Data.stringify_total_lent(*Data.get_total_lent()), Data.get_max_duration(
                end_date, "status"))
            log.persistStatus()
            exit(0)
        if int(days) > days_remaining:
            days = str(days_remaining)
    if not dry_run:
        msg = api.create_loan_offer(currency, amt, days, 0, rate)
        if days == xdays and notify_conf['notify_xday_threshold']:
            text = "{0} {1} loan placed for {2} days at a rate of {3:.4f}%".format(amt, currency, days, rate * 100)
            log.notify(text, notify_conf)
        log.offer(amt, currency, rate, days, msg)


def cancel_all():
    loan_offers = api.return_open_loan_offers()
    available_balances = api.return_available_account_balances('lending')
    for CUR in loan_offers:
        if CUR in coin_cfg and coin_cfg[CUR]['maxactive'] == 0:
            # don't cancel disabled coin
            continue
        if keep_stuck_orders:
            lending_balances = available_balances['lending']
            if isinstance(lending_balances, dict) and CUR in lending_balances:
                cur_sum = float(available_balances['lending'][CUR])
            else:
                cur_sum = 0
            for offer in loan_offers[CUR]:
                cur_sum += float(offer['amount'])
        else:
            cur_sum = float(get_min_loan_size(CUR)) + 1
        if cur_sum >= float(get_min_loan_size(CUR)):
            for offer in loan_offers[CUR]:
                if not dry_run:
                    try:
                        msg = api.cancel_loan_offer(CUR, offer['id'])
                        log.cancelOrder(CUR, msg)
                    except Exception as ex:
                        ex.message = ex.message if ex.message else str(ex)
                        log.log("Error canceling loan offer: {0}".format(ex.message))
        else:
            print "Not enough " + CUR + " to lend if bot canceled open orders. Not cancelling."


def lend_all():
    total_lent = Data.get_total_lent()[0]
    lending_balances = api.return_available_account_balances("lending")['lending']
    if dry_run:  # just fake some numbers, if dryrun (testing)
        lending_balances = Data.get_on_order_balances()

    # Fill the (maxToLend) balances on the botlog.json for display it on the web
    for cur in sorted(total_lent):
        if len(lending_balances) == 0 or cur not in lending_balances:
            MaxToLend.amount_to_lend(total_lent[cur], cur, 0, 0)
    usable_currencies = 0
    global sleep_time  # We need global var to edit sleeptime
    if gap_mode_default == "rawbtc":
        ticker = api.return_ticker()  # Only call ticker once for all orders
    else:
        ticker = False
        for cur1 in coin_cfg:
            if "rawbtc" in cur1:
                ticker = api.return_ticker()
            break
    try:
        for cur in lending_balances:
            if cur in all_currencies:
                usable_currencies += lend_cur(cur, total_lent, lending_balances, ticker)
    except StopIteration:  # Restart lending if we stop to raise the request limit.
        lend_all()
    set_sleep_time(usable_currencies)


def get_frr_or_min_daily_rate(cur):
    """
    Checks the Flash Return Rate of cur against the min daily rate and returns the better of the two. If not using
    bitfinex then it will always return the min daily rate for the currency.

    :param cur: The currency which to check
    :return: The better of the two rates (FRR and min daily rate)
    """
    if cur in coin_cfg:
        min_daily_rate = Decimal(coin_cfg[cur]['minrate'])
        frrasmin = coin_cfg[cur]['frrasmin']
        frrdelta = Decimal(coin_cfg[cur]['frrdelta']) / 100
    else:
        min_daily_rate = Decimal(Config.get("BOT", "mindailyrate", None, 0.003, 5)) / 100
        frrasmin = Config.getboolean('BOT', 'frrasmin', False)
        frrdelta = Decimal(Config.get('BOT', 'frrdelta', 0.0000))

    if exchange == 'BITFINEX' and frrasmin:
        frr_rate = Decimal(api.get_frr(cur)) + frrdelta
        if frr_rate > min_daily_rate:
            log.log("Using FRR as mindailyrate {0}% for {1}".format(frr_rate * 100, cur))
            return frr_rate

    return min_daily_rate


def get_min_daily_rate(cur):
    cur_min_daily_rate = get_frr_or_min_daily_rate(cur)
    if cur in coin_cfg:
        if coin_cfg[cur]['maxactive'] == 0:
            if cur not in max_active_alerted:  # Only alert once per coin.
                max_active_alerted[cur] = True
                log.log('maxactive amount for ' + cur + ' set to 0, won\'t lend.')
            return False
        if cur not in coin_cfg_alerted:  # Only alert once per coin.
            coin_cfg_alerted[cur] = True
            log.log('Using custom mindailyrate ' + str(cur_min_daily_rate * 100) + '% for ' + cur)
    if Analysis and cur in currencies_to_analyse:
        recommended_min = Analysis.get_rate_suggestion(cur, method=analysis_method)
        if cur_min_daily_rate < recommended_min:
            log.log("Using {0} as mindailyrate {1}% for {2}".format(analysis_method, recommended_min * 100, cur))
            cur_min_daily_rate = recommended_min
    return Decimal(cur_min_daily_rate)


def construct_order_book(active_cur):
    # make sure we have a request limit for this currency
    if active_cur not in loanOrdersRequestLimit:
        loanOrdersRequestLimit[active_cur] = defaultLoanOrdersRequestLimit

    loans = api.return_loan_orders(active_cur, loanOrdersRequestLimit[active_cur])
    if len(loans) == 0:
        return False

    rate_book = []
    volume_book = []
    for offer in loans['offers']:
        rate_book.append(offer['rate'])
        volume_book.append(offer['amount'])
    return {'rates': rate_book, 'volumes': volume_book}


def get_gap_rate(active_cur, gap, order_book, cur_total_balance, raw=False):
    if raw:
        gap_expected = gap
    else:
        gap_expected = gap * cur_total_balance / Decimal(100.0)
    gap_sum = 0
    i = 0
    while gap_sum < gap_expected:
        if i == len(order_book['volumes']) - 1 and len(order_book['volumes']) == loanOrdersRequestLimit[active_cur]:
            loanOrdersRequestLimit[active_cur] += defaultLoanOrdersRequestLimit
            log.log(active_cur + ': Not enough offers in response, adjusting request limit to ' + str(
                loanOrdersRequestLimit[active_cur]))
            raise StopIteration
        elif i == len(order_book['volumes']) - 1:
            return max_daily_rate
        gap_sum += float(order_book['volumes'][i])
        i += 1
    return Decimal(order_book['rates'][i])


def get_cur_spread(spread, cur_active_bal, active_cur):
    cur_spread_lend = int(spread)  # Checks if active_bal can't be spread that many times, and may go down to 1.
    cur_min_loan_size = get_min_loan_size(active_cur)
    while cur_active_bal < (cur_spread_lend * cur_min_loan_size):
        cur_spread_lend -= 1
    return int(cur_spread_lend)


def construct_orders(cur, cur_active_bal, cur_total_balance, ticker):
    cur_spread = get_cur_spread(spread_lend, cur_active_bal, cur)
    top_rate, bottom_rate = get_gap_mode_rates(cur, cur_active_bal, cur_total_balance, ticker)
    gap_diff = top_rate - bottom_rate
    if cur_spread == 1:
        rate_step = 0
    else:
        rate_step = gap_diff / (cur_spread - 1)

    order_rates = []
    i = 0
    while i < cur_spread:
        new_rate = bottom_rate + (rate_step * i)
        order_rates.append(new_rate)
        i += 1
    # Condensing and logic'ing time
    for rate in order_rates:
        if rate > max_daily_rate:
            order_rates.remove(rate)
            order_rates.append(max_daily_rate)
    new_order_rates = sorted(list(set(order_rates)))
    new_order_amounts = []
    i = 0
    while i < len(new_order_rates):
        new_amount = Data.truncate(cur_active_bal / len(new_order_rates), 8)
        new_order_amounts.append(Decimal(new_amount))
        i += 1
    remainder = cur_active_bal - sum(new_order_amounts)
    if remainder > 0:  # If truncating causes remainder, add that to first order.
        new_order_amounts[0] += remainder
    return {'amounts': new_order_amounts, 'rates': new_order_rates}


def get_gap_mode_rates(cur, cur_active_bal, cur_total_balance, ticker):
    global gap_mode_default, gap_bottom_default, gap_top_default  # To be able to change them later if needed.
    gap_mode, gap_bottom, gap_top = gap_mode_default, gap_bottom_default, gap_top_default
    use_gap_cfg = False
    order_book = construct_order_book(cur)
    if cur in coin_cfg:  # Get custom values specific to coin
        cfg = coin_cfg[cur]
        if cfg.get('gapmode', False) and cfg.get('gapbottom', False) and cfg.get('gaptop', False):
            # Only overwrite default if all three are set
            use_gap_cfg = True
            gap_mode = cfg['gapmode']
            gap_bottom = cfg['gapbottom']
            gap_top = cfg['gaptop']
    if gap_mode == "rawbtc":
        btc_value = 1
        if cur != 'BTC':
            for coin in ticker:
                if coin == 'BTC_' + str(cur).upper():
                    btc_value = Decimal(ticker[coin]['last'])
                    break
        bottom_depth = gap_bottom / btc_value  # Converts from BTC to altcoin's value
        bottom_rate = get_gap_rate(cur, bottom_depth, order_book, cur_total_balance, True)
        top_depth = gap_top / btc_value
        top_rate = get_gap_rate(cur, top_depth, order_book, cur_total_balance, True)
    elif gap_mode == "raw":  # Value stays in altcoin
        bottom_rate = get_gap_rate(cur, gap_bottom, order_book, cur_total_balance, True)
        top_rate = get_gap_rate(cur, gap_top, order_book, cur_total_balance, True)
    elif gap_mode == "relative":
        bottom_rate = get_gap_rate(cur, gap_bottom, order_book, cur_total_balance)
        top_rate = get_gap_rate(cur, gap_top, order_book, cur_total_balance)
    else:
        if use_gap_cfg:
            print "WARN: Invalid setting for gapMode for [%s], using defaults..." % cur
            coin_cfg[cur]['gapmode'] = "rawbtc"
            coin_cfg[cur]['gapbottom'] = 10
            coin_cfg[cur]['gaptop'] = 100
        else:
            print "WARN: Invalid setting for gapMode, using defaults..."
            gap_mode_default = "relative"
            gap_bottom_default = 10
            gap_top_default = 200
        return get_gap_mode_rates(cur, cur_active_bal, cur_total_balance, ticker)  # Start over with new defaults
    return [Decimal(top_rate), Decimal(bottom_rate)]


def lend_cur(active_cur, total_lent, lending_balances, ticker):

    active_cur_total_balance = Decimal(lending_balances[active_cur])
    if active_cur in total_lent:
        active_cur_total_balance += Decimal(total_lent[active_cur])

    # min daily rate can be changed per currency
    cur_min_daily_rate = get_min_daily_rate(active_cur)

    # log total coin
    log.updateStatusValue(active_cur, "totalCoins", (Decimal(active_cur_total_balance)))
    order_book = construct_order_book(active_cur)
    if not order_book or len(order_book['rates']) == 0 or not cur_min_daily_rate:
        return 0

    active_bal = MaxToLend.amount_to_lend(active_cur_total_balance, active_cur, Decimal(lending_balances[active_cur]),
                                          Decimal(order_book['rates'][0]))

    if float(active_bal) >= get_min_loan_size(active_cur):  # Make sure sleeptimer is set to active if any cur can lend.
        currency_usable = 1
    else:
        return 0  # Return early to end function.

    orders = construct_orders(active_cur, active_bal, active_cur_total_balance, ticker)  # Build all potential orders
    i = 0
    while i < len(orders['amounts']):  # Iterate through prepped orders and create them if they work
        below_min = Decimal(orders['rates'][i]) < Decimal(cur_min_daily_rate)

        if hide_coins and below_min:
            log.log("Not lending {:s} due to rate below {:.4f}% (actual: {:.4f}%)"
                    .format(active_cur, (cur_min_daily_rate * 100), (orders['rates'][i] * 100)))
            return 0
        elif below_min:
            rate = str(cur_min_daily_rate)
        else:
            rate = orders['rates'][i]

        try:
            create_lend_offer(active_cur, orders['amounts'][i], rate)
        except Exception as msg:
            if "Amount must be at least " in str(msg):
                import re
                results = re.findall('[-+]?([0-9]*\.[0-9]+|[0-9]+)', str(msg))
                for result in results:
                    if result:
                        min_loan_sizes[active_cur] = float(result)
                        log.log(active_cur + "'s min_loan_size has been increased to the detected min: " + result)
                return lend_cur(active_cur, total_lent, lending_balances, ticker)  # Redo cur with new min.
            else:
                raise msg

        i += 1  # Finally, move to next order.
    return currency_usable


def transfer_balances():
    # Transfers all balances on the included list to Lending.
    if len(transferable_currencies) > 0:
        exchange_balances = api.return_balances()  # This grabs only exchange balances.
        for coin in transferable_currencies:
            if coin in exchange_balances and Decimal(
                    exchange_balances[coin]) > 0:
                msg = api.transfer_balance(coin, exchange_balances[coin], 'exchange', 'lending')
                log.log(log.digestApiMsg(msg))
                log.notify(log.digestApiMsg(msg), notify_conf)
            if coin not in exchange_balances:
                print "WARN: Incorrect coin entered for transferCurrencies: " + coin
                transferable_currencies.remove(coin)
