# coding=utf-8
import argparse
import os
import sys
import time
import traceback
from decimal import Decimal
from httplib import BadStatusLine
from urllib2 import URLError

from modules.Configuration import Config
import modules.Data as Data
import modules.Lending as Lending
import modules.MaxToLend as MaxToLend
from modules.Logger import Logger
import modules.PluginsManager as PluginsManager
from modules.ExchangeApiFactory import ExchangeApiFactory
from modules.ExchangeApi import ApiError


try:
    open('lendingbot.py', 'r')
except IOError:
    os.chdir(os.path.dirname(sys.argv[0]))  # Allow relative paths

parser = argparse.ArgumentParser()  # Start args.
parser.add_argument("-cfg", "--config", help="Location of custom configuration file, overrides settings below")
parser.add_argument("-dry", "--dryrun", help="Make pretend orders", action="store_true")
args = parser.parse_args()  # End args.

# Start handling args.
dry_run = bool(args.dryrun)
if args.config:
    config_location = args.config
else:
    config_location = 'default.cfg'
# End handling args.

# Config format: Config.get(category, option, default_value=False, lower_limit=False, upper_limit=False)
# A default_value "None" means that the option is required and the bot will not run without it.
# Do not use lower or upper limit on any config options which are not numbers.
# Define the variable from the option in the module where you use it.

config = Config(config_location)

# Configure web server
if config.bot['web_server_enabled']:
    if config.bot['json_output_enabled'] is False:
        # User wants webserver enabled. Must have JSON enabled. Force logging with defaults.
        config.bot['json_output_enabled'] = True

    from modules.FlaskServer import FlaskServer
    WebServer = FlaskServer(config)
    WebServer.run_web_server()

# Configure logging
log = Logger(config.bot['jsonfile'], Decimal(config.bot['jsonlogsize'], config.bot['exchange']))

# initialize the remaining stuff
api = ExchangeApiFactory.createApi(config.bot['exchange'], config, log)  # TODO Does factory need the whole cfg?
MaxToLend.init(config, log)
Data.init(api, log)
config = Config(config_location, Data)
# config.init(config_location, Data)
if config.bot['analyseCurrencies']:
    from modules.MarketAnalysis import MarketAnalysis
    # Analysis.init(config, api, Data)
    analysis = MarketAnalysis(config, api)
    analysis.run()
else:
    analysis = None
Lending.init(config, api, log, Data, MaxToLend, dry_run, analysis, config.bot['notify_conf'])

# load plugins
PluginsManager.init(config, api, log, config.bot['notify_conf'])

print 'Welcome to ' + config.bot['label'] + ' on ' + config.bot['exchange']

try:
    while True:
        try:
            Data.update_conversion_rates(config.bot['output_currency'], config.bot['json_output_enabled'])
            PluginsManager.before_lending()
            Lending.transfer_balances()
            Lending.cancel_all()
            Lending.lend_all()
            PluginsManager.after_lending()
            log.refreshStatus(Data.stringify_total_lent(*Data.get_total_lent()),
                              Data.get_max_duration(config.bot['end_date'], "status"))
            log.persistStatus()
            sys.stdout.flush()
            time.sleep(Lending.get_sleep_time())
        except KeyboardInterrupt:
            # allow existing the main bot loop
            raise
        except Exception as ex:
            log.log_error(ex.message)
            log.persistStatus()
            if 'Invalid API key' in ex.message:
                print "!!! Troubleshooting !!!"
                print "Are your API keys correct? No quotation. Just plain keys."
                exit(1)
            elif 'Nonce must be greater' in ex.message:
                print "!!! Troubleshooting !!!"
                print "Are you reusing the API key in multiple applications? Use a unique key for every application."
                exit(1)
            elif 'Permission denied' in ex.message:
                print "!!! Troubleshooting !!!"
                print "Are you using IP filter on the key? Maybe your IP changed?"
                exit(1)
            elif 'timed out' in ex.message:
                print "Timed out, will retry in " + str(Lending.get_sleep_time()) + "sec"
            elif isinstance(ex, BadStatusLine):
                print "Caught BadStatusLine exception from Poloniex, ignoring."
            elif 'Error 429' in ex.message:
                additional_sleep = max(130.0-Lending.get_sleep_time(), 0)
                sum_sleep = additional_sleep + Lending.get_sleep_time()
                log.log_error('IP has been banned due to many requests. Sleeping for {} seconds'.format(sum_sleep))
                if config.bot['analyseCurrencies']:
                    if api.req_period <= api.default_req_period * 1.5:
                        api.req_period += 3
                    if config.bot['ma_debug_log']:
                        print("Caught ERR_RATE_LIMIT, sleeping capture and increasing request delay. Current"
                              " {0}ms".format(api.req_period))
                        log.log_error('Expect this 130s ban periodically when using MarketAnalysis, it will fix itself')
                time.sleep(additional_sleep)
            # Ignore all 5xx errors (server error) as we can't do anything about it (https://httpstatuses.com/)
            elif isinstance(ex, URLError):
                print "Caught {0} from exchange, ignoring.".format(ex.message)
            elif isinstance(ex, ApiError):
                print "Caught {0} reading from exchange API, ignoring.".format(ex.message)
            else:
                print traceback.format_exc()
                print "v{0} Unhandled error, please open a Github issue so we can fix it!".format(Data.get_bot_version())
                if config.bot['notify_conf']['notify_caught_exception']:
                    log.notify("{0}\n-------\n{1}".format(ex, traceback.format_exc()), config.bot['notify_conf'])
            sys.stdout.flush()
            time.sleep(Lending.get_sleep_time())


except KeyboardInterrupt:
    if web_server_enabled:
        WebServer.stop_web_server()
    PluginsManager.on_bot_exit()
    log.log('bye')
    print 'bye'
    os._exit(0)  # Ad-hoc solution in place of 'exit(0)' TODO: Find out why non-daemon thread(s) are hanging on exit
