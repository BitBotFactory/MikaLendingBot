# coding=utf-8
from decimal import Decimal
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
gap_bottom = 0
gap_top = 0
xday_threshold = 0
xdays = 0
min_loan_size = 0
end_date = None
coin_cfg = None
dry_run = 0
transferable_currencies = []
keep_stuck_orders = True
hide_coins = True

# limit of orders to request
loanOrdersRequestLimit = {}
defaultLoanOrdersRequestLimit = 200


def init(cfg, api1, log1, data, maxtolend, dry_run1, analysis):
    global Config, api, log, Data, MaxToLend, Analysis
    Config = cfg
    api = api1
    log = log1
    Data = data
    MaxToLend = maxtolend
    Analysis = analysis

    global sleep_time, sleep_time_active, sleep_time_inactive, min_daily_rate, max_daily_rate, spread_lend, \
        gap_bottom, gap_top, xday_threshold, xdays, min_loan_size, end_date, coin_cfg, dry_run, \
        transferable_currencies, keep_stuck_orders, hide_coins

    sleep_time_active = float(Config.get("BOT", "sleeptimeactive", None, 1, 3600))
    sleep_time_inactive = float(Config.get("BOT", "sleeptimeinactive", None, 1, 3600))
    min_daily_rate = Decimal(Config.get("BOT", "mindailyrate", None, 0.003, 5)) / 100
    max_daily_rate = Decimal(Config.get("BOT", "maxdailyrate", None, 0.003, 5)) / 100
    spread_lend = int(Config.get("BOT", "spreadlend", None, 1, 20))
    gap_bottom = Decimal(Config.get("BOT", "gapbottom", None, 0))
    gap_top = Decimal(Config.get("BOT", "gaptop", None, 0))
    xday_threshold = Decimal(Config.get("BOT", "xdaythreshold", None, 0.003, 5)) / 100
    xdays = str(Config.get("BOT", "xdays", None, 2, 60))
    min_loan_size = Decimal(Config.get("BOT", 'minloansize', None, 0.001))
    end_date = Config.get('BOT', 'endDate')
    coin_cfg = Config.get_coin_cfg()
    dry_run = dry_run1
    transferable_currencies = Config.get_currencies_list('transferableCurrencies')
    keep_stuck_orders = Config.getboolean('BOT', "keepstuckorders", True)
    hide_coins = Config.getboolean('BOT', 'hideCoins', True)

    sleep_time = sleep_time_active  # Start with active mode


def get_sleep_time():
    return sleep_time


def create_lend_offer(currency, amt, rate):
    days = '2'
    # if (min_daily_rate - 0.000001) < rate and Decimal(amt) > min_loan_size:
    if float(amt) > min_loan_size:
        if float(rate) > 0.0001:
            rate = float(rate) - 0.000001  # lend offer just bellow the competing one
        amt = "%.8f" % Decimal(amt)
        if float(rate) > xday_threshold:
            days = xdays
        if xday_threshold == 0:
            days = '2'
        if Config.has_option('BOT', 'endDate'):
            days_remaining = int(Data.get_max_duration(end_date, "order"))
            if int(days_remaining) <= 2:
                print "endDate reached. Bot can no longer lend.\nExiting..."
                log.log("The end date has almost been reached and the bot can no longer lend. Exiting.")
                log.refreshStatus(Data.stringify_total_lended(*Data.get_total_lended()), Data.get_max_duration(
                    end_date, "status"))
                log.persistStatus()
                exit(0)
            if int(days) > days_remaining:
                days = str(days_remaining)
        if not dry_run:
            msg = api.create_loan_offer(currency, amt, days, 0, rate)
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
            cur_sum = float(min_loan_size) + 1
        if cur_sum >= float(min_loan_size):
            for offer in loan_offers[CUR]:
                if not dry_run:
                    try:
                        msg = api.cancel_loan_offer(CUR, offer['id'])
                        log.cancelOrders(CUR, msg)
                    except Exception as Ex:
                        log.log("Error canceling loan offer: " + str(Ex))
        else:
            print "Not enough " + CUR + " to lend if bot canceled open orders. Not cancelling."


def lend_all():
    total_lended = Data.get_total_lended()[0]
    lending_balances = api.return_available_account_balances("lending")['lending']
    if dry_run:  # just fake some numbers, if dryrun (testing)
        lending_balances.update(Data.get_on_order_balances())

    # Fill the (maxToLend) balances on the botlog.json for display it on the web
    for key in sorted(total_lended):
        if len(lending_balances) == 0 or key not in lending_balances:
            MaxToLend.amount_to_lend(total_lended[key], key, 0, 0)
    usable_currencies = 0
    global sleep_time  # We need global var to edit sleeptime
    for cur in lending_balances:
        usable_currencies += lend_cur(cur, total_lended, lending_balances)
    if usable_currencies == 0:  # After loop, if no currencies had enough to lend, use inactive sleep time.
        sleep_time = sleep_time_inactive
    else:  # Else, use active sleep time.
        sleep_time = sleep_time_active


def lend_cur(active_cur, total_lended, lending_balances):
    currency_usable = 0
    active_cur_test_balance = Decimal(lending_balances[active_cur])
    if active_cur in total_lended:
        active_cur_test_balance += Decimal(total_lended[active_cur])

    # min daily rate can be changed per currency
    cur_min_daily_rate = min_daily_rate
    if active_cur in coin_cfg:
        if coin_cfg[active_cur]['maxactive'] == 0:
            log.log('maxactive amount for ' + active_cur + ' set to 0, won\'t lend.')
            return 0
        cur_min_daily_rate = coin_cfg[active_cur]['minrate']
        log.log('Using custom mindailyrate ' + str(coin_cfg[active_cur]['minrate'] * 100) + '% for ' + active_cur)
    if Analysis:
        recommended_min = Analysis.get_rate_suggestion(active_cur)
        if cur_min_daily_rate < recommended_min:
            cur_min_daily_rate = recommended_min

    # log total coin
    log.updateStatusValue(active_cur, "totalCoins", (Decimal(active_cur_test_balance)))

    # make sure we have a request limit for this currency
    if active_cur not in loanOrdersRequestLimit:
        loanOrdersRequestLimit[active_cur] = defaultLoanOrdersRequestLimit

    loans = api.return_loan_orders(active_cur, loanOrdersRequestLimit[active_cur])
    loans_length = len(loans['offers'])
    if hide_coins and Decimal(loans['offers'][0]['rate']) < Decimal(cur_min_daily_rate):
        log.log("Not lending " + active_cur + " due to low rate.")
        return 0

    active_bal = MaxToLend.amount_to_lend(active_cur_test_balance, active_cur,
                                          Decimal(lending_balances[active_cur]),
                                          Decimal(loans['offers'][0]['rate']))

    if float(active_bal) > min_loan_size:  # Make sure sleeptimer is set to active if any currencies can lend.
        currency_usable = 1
    else:
        return currency_usable  # Return early to end function.

    lower_sum = Decimal(0)  # sum
    order_num = int(0)  # offer book iterator
    spread_steps = int(0)  # spread step count
    lent = Decimal(0)
    # in case of empty lendbook, lend at max
    cur_spread_lend = int(spread_lend)  # Checks if active_bal can't be spread that many times, and may go down to 1.
    while active_bal < (cur_spread_lend * min_loan_size):
        cur_spread_lend -= 1
    step_pct = (gap_top - gap_bottom) / cur_spread_lend

    active_plus_lended = Decimal(active_bal)
    if active_cur in total_lended:
        active_plus_lended += Decimal(total_lended[active_cur])
    if loans_length == 0:
        create_lend_offer(active_cur, Decimal(active_bal) - lent, max_daily_rate)
    for offer in loans['offers']:
        lower_sum += Decimal(offer['amount'])
        upper_sum = lower_sum
        while True:
            sum_diff = upper_sum - lower_sum
            gap_multiplier = gap_bottom / 100 + (step_pct / 100 * spread_steps)
            if upper_sum > active_plus_lended * gap_multiplier and Decimal(offer['rate']) > cur_min_daily_rate:
                spread_steps += 1
                upper_sum += Decimal(active_bal) / cur_spread_lend
            else:
                create_lend_offer(active_cur, sum_diff, offer['rate'])
                lent += sum_diff.quantize(SATOSHI)
                break
            if spread_steps == cur_spread_lend:
                create_lend_offer(active_cur, Decimal(active_bal) - lent, offer['rate'])
                break
        if spread_steps == cur_spread_lend:
            break
        order_num += 1
        if order_num == loans_length:  # end of the offers
            if loans_length < loanOrdersRequestLimit[active_cur]:
                # lend at max
                create_lend_offer(active_cur, Decimal(active_bal) - lent, max_daily_rate)
            else:
                # increase limit for currency to get a more accurate response
                loanOrdersRequestLimit[active_cur] += defaultLoanOrdersRequestLimit
                log.log(active_cur + ': Not enough offers in response, adjusting request limit to ' + str(
                    loanOrdersRequestLimit[active_cur]))
                # repeat currency
                lend_cur(active_cur, total_lended, lending_balances)
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
            if coin not in exchange_balances:
                print "ERROR: Incorrect coin entered for transferCurrencies: " + coin


def set_auto_renew(auto):
    i = int(0)  # counter
    try:
        action = 'Clearing'
        if auto == 1:
            action = 'Setting'
        log.log(action + ' AutoRenew...(Please Wait)')
        crypto_lended = api.return_active_loans()
        loans_count = len(crypto_lended["provided"])
        for item in crypto_lended["provided"]:
            if int(item["autoRenew"]) != auto:
                log.refreshStatus('Processing AutoRenew - ' + str(i) + ' of ' + str(loans_count) + ' loans')
                api.toggle_auto_renew(int(item["id"]))
                i += 1
    except KeyboardInterrupt:
        log.log('Toggled AutoRenew for ' + str(i) + ' loans')
        raise SystemExit
    log.log('Toggled AutoRenew for ' + str(i) + ' loans')
