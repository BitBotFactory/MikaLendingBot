# coding=utf-8
import argparse
import datetime
import json
import shutil
import sys
import time
import traceback
from ConfigParser import SafeConfigParser
from decimal import *

from Logger import Logger
from poloniex import Poloniex

SATOSHI = Decimal(10) ** -8

config = SafeConfigParser()
config_location = 'default.cfg'

# Defaults
min_loan_size = 0.001

parser = argparse.ArgumentParser()  # Start args.
parser.add_argument("-cfg", "--config", help="Location of custom configuration file, overrides settings below")
parser.add_argument("-dry", "--dryrun", help="Make pretend orders", action="store_true")
parser.add_argument("-clrrenew", "--clearautorenew", help="Stops all autorenew orders", action="store_true")
parser.add_argument("-setrenew", "--setautorenew", help="Sets all orders to autorenew", action="store_true")
parser.add_argument("-key", "--apikey", help="Account API key, should be unique to this script.")
parser.add_argument("-secret", "--apisecret", help="Account API secret, should be unique to this script.")
parser.add_argument("-sleepactive", "--sleeptimeactive", help="Time between active iterations, seconds")
parser.add_argument("-sleepinactive", "--sleeptimeinactive", help="Time between inactive iterations, seconds")
parser.add_argument("-minrate", "--mindailyrate", help="Minimum rate you will lend at")
parser.add_argument("-maxrate", "--maxdailyrate", help="Maximum rate you will lend at")
parser.add_argument("-spread", "--spreadlend", help="How many orders to split your lending into")
parser.add_argument("-gapbot", "--gapbottom",
                    help="Percentage of your order's volume into the ledger you start lending")
parser.add_argument("-gaptop", "--gaptop", help="Percentage of your order's volume into the ledger you stop lending")
parser.add_argument("-60day", "--sixtydaythreshold",
                    help="Rate at where bot will request to lend for 60 days")  # only used for backward compatibility
parser.add_argument("-xdaythreshold", "--xdaythreshold", help="Rate at where bot will request to lend for xdays")
parser.add_argument("-xdays", "--xdays", help="the length the bot will lend if xdaythreashold is met")
parser.add_argument("-trans", "--transferablecurrencies",
                    help="A list of currencies to transfer from exchange to lending balance.")
parser.add_argument("-autorenew", "--autorenew", help="Sets autorenew on bot stop, and clears autorenew on start",
                    action="store_true")
parser.add_argument("-minloan", "--minloansize", help='Minimum size of offers to make')
parser.add_argument("-json", "--jsonfile", help="Location of .json file to save log to")
parser.add_argument("-jsonsize", "--jsonlogsize", help="How many lines to keep saved to the json log file")
parser.add_argument("-server", "--startwebserver",
                    help="If enabled, starts a webserver for the /www/ folder on customip/lendingbot.html",
                    action="store_true")
parser.add_argument("-customip", "--customwebserveraddress", help="The webserver's ip address. Advanced users only.")
parser.add_argument("-coincfg", "--coinconfig",
                    help='Custom config per coin, useful when closing positions etc.')
parser.add_argument("-outcurr", "--outputcurrency",
                    help="The currency that the HTML Overview will present the earnings summary in.")
parser.add_argument("-maxlent", "--maxtolent",
                    help="Max amount to lent. if set to 0 the bot will check for maxpercenttolent.")
parser.add_argument("-maxplent", "--maxpercenttolent",
                    help="Max percent to lent. if set to 0 the bot will lent the 100%.")
parser.add_argument("-maxlentr", "--maxtolentrate",
                    help="Max to lent rate. The lending rate to trigger disabling maxtolent.")
args = parser.parse_args()  # End args.
# Start handling args.
if args.apikey:
    api_key = args.apikey
if args.apisecret:
    api_secret = args.apisecret
if args.sleeptimeactive:
    sleep_time_active = int(args.sleeptimeactive)
if args.sleeptimeinactive:
    sleep_time_inactive = int(args.sleeptimeinactive)
if args.mindailyrate:
    min_daily_rate = Decimal(args.mindailyrate) / 100
if args.maxdailyrate:
    max_daily_rate = Decimal(args.maxdailyrate) / 100
if args.spreadlend:
    spread_lend = int(args.spreadlend)
if args.gapbottom:
    gap_bottom = Decimal(args.gapbottom)
if args.gaptop:
    gap_top = Decimal(args.gapbottom)
if args.sixtydaythreshold:
    sixty_day_threshold = Decimal(args.sixtydaythreshold) / 100
if args.xdaythreshold:
    xday_threshold = Decimal(args.xdaythreshold) / 100
if args.xdays:
    xdays = str(args.xdays)
if args.transferablecurrencies:
    transferable_currencies = args.transferablecurrencies
if args.dryrun:
    dry_run = True
else:
    dry_run = False
if args.config:
    config_location = args.config
if args.autorenew:
    auto_renew = 1
else:
    auto_renew = 0
if args.minloansize:
    min_loan_size = Decimal(args.minloansize)
coincfg = {}
if args.coinconfig:
    coinconfig = args.coinconfig.split(',')
    for cur in coinconfig:
        cur = cur.split(':')
        coincfg[cur[0]] = dict(minrate=(Decimal(cur[1])) / 100, maxactive=Decimal(cur[2]), maxtolent=Decimal(cur[3]),
                               maxpercenttolent=(Decimal(cur[4])) / 100, maxtolentrate=(Decimal(cur[5])) / 100)
if args.outputcurrency:
    output_currency = args.outputcurrency
else:
    output_currency = 'BTC'
if args.maxtolent:
    maxtolent = Decimal(args.maxtolent)
else:
    maxtolent = 0
if args.maxpercenttolent:
    maxpercenttolent = Decimal(args.maxpercenttolent) / 100
else:
    maxpercenttolent = 0
if args.maxtolentrate:
    maxtolentrate = Decimal(args.maxtolentrate) / 100
else:
    maxtolentrate = 0
# End handling args.

# Check if we need a config file at all (If all settings are passed by args, we won't)
if args.apikey and args.apisecret and args.sleeptimeactive and args.sleeptimeinactive and args.mindailyrate and (
                        args.maxdailyrate and args.spreadlend and args.gapbottom and args.gaptop and (
                            (args.xdaythreshold and args.xdays) or args.sixtydaythreshold)):
    # If all that was true, we don't need a config file...
    config_needed = False
    print "Settings met from arguments."
else:
    config_needed = True
    print "Obtaining settings from config file."

# When true, will overwrite anything passed by args with the found cfg
if config_needed:
    loaded_files = config.read([config_location])
    # Copy default config file if not found
    if len(loaded_files) != 1:
        shutil.copy('default.cfg.example', 'default.cfg')
        print '\ndefault.cfg.example has been copied to default.cfg\nEdit it with your API key and custom settings.\n'
        raw_input("Press Enter to acknowledge and exit...")
        exit(0)

    if config.has_option('BOT', 'sleeptimeactive') and config.has_option('BOT', 'sleeptimeinactive'):
        sleep_time_active = float(config.get("BOT", "sleeptimeactive"))
        sleep_time_inactive = float(config.get("BOT", "sleeptimeinactive"))
    else:
        sleep_time = float(config.get("BOT", "sleeptime"))  # If it can't find a setting, run with the old cfg.
        sleep_time_active = sleep_time
        sleep_time_inactive = sleep_time
        print "!!! Please update to new config that includes Inactive Mode. !!!"  # Update alert.
    api_key = config.get("API", "apikey")
    api_secret = config.get("API", "secret")
    min_daily_rate = Decimal(config.get("BOT", "mindailyrate")) / 100
    max_daily_rate = Decimal(config.get("BOT", "maxdailyrate")) / 100
    spread_lend = int(config.get("BOT", "spreadlend"))
    gap_bottom = Decimal(config.get("BOT", "gapbottom"))
    gap_top = Decimal(config.get("BOT", "gaptop"))
    if config.has_option("BOT", "sixtyDayThreshold"):
        sixty_day_threshold = float(config.get("BOT", "sixtydaythreshold")) / 100
        xday_threshold = sixty_day_threshold
        xdays = "60"
    else:
        xday_threshold = Decimal(config.get("BOT", "xdaythreshold")) / 100
        xdays = str(config.get("BOT", "xdays"))
    auto_renew = int(config.get("BOT", "autorenew"))
    if config.has_option('BOT', 'outputCurrency'):
        output_currency = config.get('BOT', 'outputCurrency')
    if config.has_option('BOT', 'maxtolent'):
        maxtolent = Decimal(config.get('BOT', 'maxtolent'))
    if config.has_option('BOT', 'maxpercenttolent'):
        maxpercenttolent = Decimal(config.get('BOT', 'maxpercenttolent')) / 100
    if config.has_option('BOT', 'maxtolentrate'):
        maxtolentrate = Decimal(config.get('BOT', 'maxtolentrate')) / 100
    if config.has_option('BOT', 'minloansize'):
        min_loan_size = Decimal(config.get("BOT", 'minloansize'))
    if config.has_option('BOT', "transferableCurrencies"):
        transferable_currencies = (config.get("BOT", "transferableCurrencies")).split(",")
    else:
        transferable_currencies = []

    if config.has_option("BOT", "coinconfig"):
        try:
            # parsed
            coinconfig = (json.loads(config.get("BOT", "coinconfig")))
            for cur in coinconfig:
                cur = cur.split(':')
                coincfg[cur[0]] = dict(minrate=(Decimal(cur[1])) / 100, maxactive=Decimal(cur[2]),
                                       maxtolent=Decimal(cur[3]), maxpercenttolent=(Decimal(cur[4])) / 100,
                                       maxtolentrate=(Decimal(cur[5])) / 100)
        except Exception as e:
            print "Coinconfig parsed incorrectly, please refer to the documentation. Error: " + e
            pass

sleep_time = sleep_time_active  # Start with active mode
# sanity checks
if sleep_time < 1 or sleep_time > 3600 or sleep_time_inactive < 1 or sleep_time_inactive > 3600:
    print "sleeptime values must be 1-3600"
    exit(1)
if min_daily_rate < 0.00003 or min_daily_rate > 0.05:  # 0.003% daily is 1% yearly
    print "mindaily rate is set too low or too high, must be 0.003-5%"
    exit(1)
if max_daily_rate < 0.00003 or max_daily_rate > 0.05:
    print "maxdaily rate is set too low or too high, must be 0.003-5%"
    exit(1)
if spread_lend < 1 or spread_lend > 20:
    print "spreadlend value must be 1-20 range"
    exit(1)


def timestamp():
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

bot = Poloniex(api_key, api_secret)
log = {}

# check if json output is enabled
jsonOutputEnabled = (config.has_option('BOT', 'jsonfile') and config.has_option('BOT', 'jsonlogsize')) or (
    args.jsonfile and args.jsonlogsize)
if jsonOutputEnabled:
    if config_needed:
        jsonFile = config.get("BOT", "jsonfile")
        jsonLogSize = int(config.get("BOT", "jsonlogsize"))
    else:
        jsonFile = args.jsonfile
        jsonLogSize = args.jsonlogsize
    log = Logger(jsonFile, jsonLogSize)
else:
    log = Logger()

# total lended global variable
totalLended = {}
rateLended = {}


def refresh_total_lended():
    global totalLended, rateLended
    crypto_lended = bot.returnActiveLoans()

    totalLended = {}
    rateLended = {}

    for item in crypto_lended["provided"]:
        item_str = item["amount"].encode("utf-8")
        item_float = Decimal(item_str)
        item_rate_str = item["rate"].encode("utf-8")
        item_rate_float = Decimal(item_rate_str)
        if item["currency"] in totalLended:
            crypto_lended_sum = totalLended[item["currency"]] + item_float
            crypto_lended_rate = rateLended[item["currency"]] + (item_rate_float * item_float)
            totalLended[item["currency"]] = crypto_lended_sum
            rateLended[item["currency"]] = crypto_lended_rate
        else:
            crypto_lended_sum = item_float
            crypto_lended_rate = item_rate_float * item_float
            totalLended[item["currency"]] = crypto_lended_sum
            rateLended[item["currency"]] = crypto_lended_rate


def stringify_total_lended():
    result = 'Lended: '
    for key in sorted(totalLended):
        average_lending_rate = Decimal(rateLended[key] * 100 / totalLended[key])
        result += '[%.4f %s @ %.4f%%] ' % (Decimal(totalLended[key]), key, average_lending_rate)
        log.updateStatusValue(key, "lentSum", totalLended[key])
        log.updateStatusValue(key, "averageLendingRate", average_lending_rate)
    return result


def create_loan_offer(currency, amt, rate):
    days = '2'
    # if (min_daily_rate - 0.000001) < rate and Decimal(amt) > min_loan_size:
    if float(amt) > min_loan_size:
        rate = float(rate) - 0.000001  # lend offer just bellow the competing one
        amt = "%.8f" % Decimal(amt)
        if rate > xday_threshold:
            days = xdays
        if xday_threshold == 0:
            days = '2'
        if config.has_option('BOT', 'endDate'):
            days_remaining = int(get_max_duration("order"))
            if int(days_remaining) <= 2:
                print "endDate reached. Bot can no longer lend.\nExiting..."
                log.log("The end date has almost been reached and the bot can no longer lend. Exiting.")
                log.refreshStatus(stringify_total_lended(), get_max_duration("status"))
                log.persistStatus()
                exit(0)
            if int(days) > days_remaining:
                days = str(days_remaining)
        if not dry_run:
            msg = bot.createLoanOffer(currency, amt, days, 0, rate)
            log.offer(amt, currency, rate, days, msg)


# limit of orders to request
loanOrdersRequestLimit = {}
defaultLoanOrdersRequestLimit = 200


def amount_to_lent(active_cur_test_balance, active_cur, lending_balance, low_rate):
    restrict_lent = False
    active_bal = Decimal(0)
    log_data = str("")
    if active_cur in coincfg:
        if (coincfg[active_cur]['maxtolentrate'] == 0 and low_rate > 0 or coincfg[active_cur][
                'maxtolentrate'] >= low_rate > 0):
            log_data = ("The Lower Rate found on " + active_cur + " is " + str(
                "%.4f" % (Decimal(low_rate) * 100)) + "% vs conditional rate " + str(
                "%.4f" % (Decimal(coincfg[active_cur]['maxtolentrate']) * 100)) + "%. ")
            restrict_lent = True
        if coincfg[active_cur]['maxtolent'] != 0 and restrict_lent:
            log.updateStatusValue(active_cur, "maxToLend", coincfg[active_cur]['maxtolent'])
            if lending_balance > (active_cur_test_balance - coincfg[active_cur]['maxtolent']):
                active_bal = (lending_balance - (active_cur_test_balance - coincfg[active_cur]['maxtolent']))
        if coincfg[active_cur]['maxtolent'] == 0 and coincfg[active_cur][
                'maxpercenttolent'] != 0 and restrict_lent:
            log.updateStatusValue(active_cur, "maxToLend",
                                  (coincfg[active_cur]['maxpercenttolent'] * active_cur_test_balance))
            if (lending_balance > (
                        active_cur_test_balance - (coincfg[active_cur]['maxpercenttolent'] * active_cur_test_balance))):
                active_bal = (lending_balance - (
                    active_cur_test_balance - (coincfg[active_cur]['maxpercenttolent'] * active_cur_test_balance)))
        if coincfg[active_cur]['maxtolent'] == 0 and coincfg[active_cur]['maxpercenttolent'] == 0:
            log.updateStatusValue(active_cur, "maxToLend", active_cur_test_balance)
            active_bal = lending_balance

    if active_cur not in coincfg:
        if maxtolentrate == 0 and low_rate > 0 or maxtolentrate >= low_rate > 0:
            log_data = ("The Lower Rate found on " + active_cur + " is " + str(
                "%.4f" % (Decimal(low_rate) * 100)) + "% vs conditional rate " + str(
                "%.4f" % (Decimal(maxtolentrate) * 100)) + "%. ")
            restrict_lent = True
        if maxtolent != 0 and restrict_lent:
            log.updateStatusValue(active_cur, "maxToLend", maxtolent)
            if lending_balance > (active_cur_test_balance - maxtolent):
                active_bal = (lending_balance - (active_cur_test_balance - maxtolent))
        if maxtolent == 0 and maxpercenttolent != 0 and restrict_lent:
            log.updateStatusValue(active_cur, "maxToLend", (maxpercenttolent * active_cur_test_balance))
            if lending_balance > (active_cur_test_balance - (maxpercenttolent * active_cur_test_balance)):
                active_bal = (lending_balance - (active_cur_test_balance - (
                    maxpercenttolent * active_cur_test_balance)))
        if maxtolent == 0 and maxpercenttolent == 0:
            log.updateStatusValue(active_cur, "maxToLend", active_cur_test_balance)
            active_bal = lending_balance
    if not restrict_lent:
        log.updateStatusValue(active_cur, "maxToLend", active_cur_test_balance)
        active_bal = lending_balance
    if (lending_balance - active_bal) < min_loan_size:
        active_bal = lending_balance
    if active_bal < lending_balance:
        log.log(log_data + " Lending " + str("%.8f" % Decimal(active_bal)) + " of " + str(
            "%.8f" % Decimal(lending_balance)) + " Available")
    return active_bal


def get_open_offers():
    loan_offers = bot.returnOpenLoanOffers()
    if isinstance(loan_offers, list):  # silly api wrapper, empty dict returns a list, which breaks the code later.
        loan_offers = {}
    return loan_offers


def get_on_order_balances():
    loan_offers = get_open_offers()
    on_order_balances = {}
    for CUR in loan_offers:
        for offer in loan_offers[CUR]:
            on_order_balances[CUR] = on_order_balances.get(CUR, 0) + Decimal(offer['amount'])
    return on_order_balances


def get_max_duration(context):
    if not config.has_option('BOT', 'endDate'):
        return ""
    try:
        now_time = datetime.date.today()
        config_date = map(int, config.get('BOT', 'endDate').split(','))
        end_time = datetime.date(*config_date)  # format YEAR,MONTH,DAY all ints, also used splat operator
        diff_days = (end_time - now_time).days
        if context == "order":
            return diff_days  # Order needs int
        if context == "status":
            return " - Days Remaining: " + str(diff_days)  # Status needs string
    except Exception as E:
        print "ERROR: There is something wrong with your endDate option. Error: " + str(E)
        exit(1)


def cancel_all():
    loan_offers = get_open_offers()
    for CUR in loan_offers:
        if CUR in coincfg and coincfg[CUR]['maxactive'] == 0:
            # don't cancel disabled coin
            continue
        for offer in loan_offers[CUR]:
            if not dry_run:
                try:
                    msg = bot.cancelLoanOffer(CUR, offer['id'])
                    log.cancelOrders(CUR, msg)
                except Exception as E:
                    log.log("Error canceling loan offer: " + str(E))


def loan_all():
    lending_balances = bot.returnAvailableAccountBalances("lending")['lending']
    if dry_run:  # just fake some numbers, if dryrun (testing)
        if isinstance(lending_balances, list):  # silly api wrapper, empty dict returns a list, which breaks the code later.
            lending_balances = {}
        lending_balances.update(get_on_order_balances())

    # Fill the (maxToLend) balances on the botlog.json for display it on the web
    for key in sorted(totalLended):
        if len(lending_balances) == 0 or key not in lending_balances:
            amount_to_lent(totalLended[key], key, 0, 0)

    active_cur_index = 0
    usable_currencies = 0
    global sleep_time  # We need global var to edit sleeptime
    while active_cur_index < len(lending_balances):
        active_cur = lending_balances.keys()[active_cur_index]
        active_cur_index += 1
        active_cur_test_balance = Decimal(lending_balances[active_cur])
        if active_cur in totalLended:
            active_cur_test_balance += Decimal(totalLended[active_cur])

        # min daily rate can be changed per currency
        cur_min_daily_rate = min_daily_rate
        if active_cur in coincfg:
            if coincfg[active_cur]['maxactive'] == 0:
                log.log('maxactive amount for ' + active_cur + ' set to 0, won\'t lend.')
                continue
            cur_min_daily_rate = coincfg[active_cur]['minrate']
            log.log('Using custom mindailyrate ' + str(coincfg[active_cur]['minrate'] * 100) + '% for ' + active_cur)

        # log total coin
        log.updateStatusValue(active_cur, "totalCoins", (Decimal(active_cur_test_balance)))

        # make sure we have a request limit for this currency
        if active_cur not in loanOrdersRequestLimit:
            loanOrdersRequestLimit[active_cur] = defaultLoanOrdersRequestLimit

        loans = bot.returnLoanOrders(active_cur, loanOrdersRequestLimit[active_cur])
        loans_length = len(loans['offers'])

        active_bal = amount_to_lent(active_cur_test_balance, active_cur, Decimal(lending_balances[active_cur]),
                                    Decimal(loans['offers'][0]['rate']))

        if float(
                active_bal) > min_loan_size:  # Make sure sleeptimer is set to active if any currencies can lend.
            usable_currencies = 1
        else:
            continue

        s = Decimal(0)  # sum
        i = int(0)  # offer book iterator
        j = int(0)  # spread step count
        lent = Decimal(0)
        step = (gap_top - gap_bottom) / spread_lend
        # TODO check for minimum lendable amount, and try to decrease the spread.
        # e.g. at the moment balances lower than 0.001 won't be lent
        # in case of empty lendbook, lend at max
        active_plus_lended = Decimal(active_bal)
        if active_cur in totalLended:
            active_plus_lended += Decimal(totalLended[active_cur])
        if loans_length == 0:
            create_loan_offer(active_cur, Decimal(active_bal) - lent, max_daily_rate)
        for offer in loans['offers']:
            s = s + Decimal(offer['amount'])
            s2 = s
            while True:
                if s2 > active_plus_lended * (gap_bottom / 100 + (step / 100 * j)) and Decimal(
                        offer['rate']) > cur_min_daily_rate:
                    j += 1
                    s2 += Decimal(active_bal) / spread_lend
                else:
                    create_loan_offer(active_cur, s2 - s, offer['rate'])
                    lent = lent + (s2 - s).quantize(SATOSHI)
                    break
                if j == spread_lend:
                    create_loan_offer(active_cur, Decimal(active_bal) - lent, offer['rate'])
                    break
            if j == spread_lend:
                break
            i += 1
            if i == loans_length:  # end of the offers
                if loans_length < loanOrdersRequestLimit[active_cur]:
                    # lend at max
                    create_loan_offer(active_cur, Decimal(active_bal) - lent, max_daily_rate)
                else:
                    # increase limit for currency to get a more accurate response
                    loanOrdersRequestLimit[active_cur] += defaultLoanOrdersRequestLimit
                    log.log(active_cur + ': Not enough offers in response, adjusting request limit to ' + str(
                        loanOrdersRequestLimit[active_cur]))
                    # repeat currency
                    active_cur_index -= 1
    if usable_currencies == 0:  # After loop, if no currencies had enough to lend, use inactive sleep time.
        sleep_time = sleep_time_inactive
    else:  # Else, use active sleep time.
        sleep_time = sleep_time_active


def set_auto_renew(auto):
    i = int(0)  # counter
    try:
        action = 'Clearing'
        if auto == 1:
            action = 'Setting'
        log.log(action + ' AutoRenew...(Please Wait)')
        crypto_lended = bot.returnActiveLoans()
        loans_count = len(crypto_lended["provided"])
        for item in crypto_lended["provided"]:
            if int(item["autoRenew"]) != auto:
                log.refreshStatus('Processing AutoRenew - ' + str(i) + ' of ' + str(loans_count) + ' loans')
                bot.toggleAutoRenew(int(item["id"]))
                i += 1
    except KeyboardInterrupt:
        log.log('Toggled AutoRenew for ' + str(i) + ' loans')
        raise SystemExit
    log.log('Toggled AutoRenew for ' + str(i) + ' loans')


server = None


def start_web_server():
    import SimpleHTTPServer
    import SocketServer

    try:
        port = int(web_server_port)
        host = web_server_ip

        # Do not attempt to fix code warnings in the below class, it is perfect.
        class QuietHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
            # quiet server logs
            def log_message(self, format, *args):
                return

            # serve from www folder under current working dir
            def translate_path(self, path):
                return SimpleHTTPServer.SimpleHTTPRequestHandler.translate_path(self, '/www' + path)

        global server
        server = SocketServer.TCPServer((host, port), QuietHandler)
        if host == "0.0.0.0":
            host1 = "localhost"
        else:
            host1 = host
        print 'Started WebServer, lendingbot status available at http://' + host1 + ':' + str(port) + '/lendingbot.html'
        server.serve_forever()
    except Exception as E:
        print 'Failed to start WebServer' + str(E)


def update_conversion_rates():
    global jsonOutputEnabled, totalLended
    if jsonOutputEnabled:
        ticker_response = bot.returnTicker()
        for couple in ticker_response:
            currencies = couple.split('_')
            ref = currencies[0]
            currency = currencies[1]
            if ref == 'BTC' and currency in totalLended:
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


def transfer_balances():
    # Transfers all balances on the included list to Lending.
    # transferable_currencies = config list of currencies.
    if len(transferable_currencies) > 0:
        exchange_balances = bot.returnBalances()  # This grabs only exchange balances.
        for rawcoin in transferable_currencies:
            coin = rawcoin.strip().upper()  # Make sure spaces and caps don't break everything.
            if coin in exchange_balances and Decimal(
                    exchange_balances[coin]) > 0:  # Check if coin has an outstanding balance.
                msg = bot.transferBalance(coin, exchange_balances[coin], 'exchange', 'lending')
                log.log(log.digestApiMsg(msg))
            if coin not in exchange_balances:
                print "ERROR: Incorrect coin entered for transferCurrencies: " + coin


# Parse these down here...
if args.clearautorenew:
    set_auto_renew(0)
    raise SystemExit
if args.setautorenew:
    set_auto_renew(1)
    raise SystemExit


def stop_web_server():
    try:
        print "Stopping WebServer"
        server.shutdown()
    except Exception as ex:
        print 'Failed to stop WebServer' + str(ex)


print 'Welcome to Poloniex Lending Bot'
if config_needed:  # Configure webserver
    web_server_enabled = config.has_option('BOT', 'startWebServer') and config.getboolean('BOT', 'startWebServer')
    if config.has_option('BOT', 'customWebServerAddress'):
        custom_web_server_address = (config.get('BOT', 'customWebServerAddress').split(':'))
        if len(custom_web_server_address) == 1:
            custom_web_server_address.append("8000")
            print "WARNING: Please specify a port for the webserver in the form IP:PORT, default port 8000 used."
    else:
        custom_web_server_address = ['0.0.0.0', '8000']
else:
    web_server_enabled = args.startwebserver
    if args.customwebserveraddress:
        custom_web_server_address = args.customwebserveraddress
    else:
        custom_web_server_address = ['0.0.0.0', '8000']
web_server_ip = custom_web_server_address[0]
web_server_port = custom_web_server_address[1]

if web_server_enabled:  # Run webserver
    import threading

    thread = threading.Thread(target=start_web_server)
    thread.deamon = True
    thread.start()

# if config includes autorenew - start by clearing the current loans
if auto_renew == 1:
    set_auto_renew(0)

try:
    while True:
        try:
            refresh_total_lended()
            update_conversion_rates()
            transfer_balances()
            cancel_all()
            loan_all()
            log.refreshStatus(stringify_total_lended(), get_max_duration("status"))
            log.persistStatus()
            sys.stdout.flush()
            time.sleep(sleep_time)
        except Exception as e:
            log.log("ERROR: " + str(e))
            log.persistStatus()
            print timestamp()
            print traceback.format_exc()
            if 'Invalid API key' in str(e):
                print "!!! Troubleshooting !!!"
                print "Are your API keys correct? No quotation. Just plain keys."
                exit(1)
            if 'Nonce must be greater' in str(e):
                print "!!! Troubleshooting !!!"
                print "Are you reusing the API key in multiple applications? use a unique key for every application."
                exit(1)
            if 'Permission denied' in str(e):
                print "!!! Troubleshooting !!!"
                print "Are you using IP filter on the key? Maybe your IP changed?"
                exit(1)
            sys.stdout.flush()
            time.sleep(sleep_time)
            pass
except KeyboardInterrupt:
    if auto_renew == 1:
        set_auto_renew(1)
    if web_server_enabled:
        stop_web_server()
    log.log('bye')
    exit(0)
