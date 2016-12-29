# coding=utf-8
import argparse
import datetime
import sys
import time
import traceback

from modules.Logger import Logger
from modules.Poloniex import Poloniex
import modules.Configuration as Config
import modules.MaxToLend as MaxToLend
import modules.Data as Data
import modules.Lending as Lending


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

Config.init([config_location])
# Config format: Config.get(category, option, default_value=False, lower_limit=False, upper_limit=False)
# A default_value "None" means that the option is required and the bot will not run without it.
# Do not use lower or upper limit on any config options which are not numbers.
# Define the variable from the option in the module where you use it.
api_key = Config.get("API", "apikey", None)
api_secret = Config.get("API", "secret", None)
output_currency = Config.get('BOT', 'outputCurrency', 'BTC')
end_date = Config.get('BOT', 'endDate')
json_output_enabled = Config.has_option('BOT', 'jsonfile') and Config.has_option('BOT', 'jsonlogsize')


def timestamp():
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


log = Logger(Config.get('BOT', 'jsonfile', ''), Config.get('BOT', 'jsonlogsize', -1))
api = Poloniex(api_key, api_secret)
MaxToLend.init(Config, log)
Data.init(api, log)
Lending.init(Config, api, log, Data, MaxToLend, dry_run)


print 'Welcome to Poloniex Lending Bot'
# Configure web server

web_server_enabled = Config.get('BOT', 'startWebServer')
if web_server_enabled:  # Run web server
    import modules.WebServer as WebServer
    WebServer.initialize_web_server(Config)

try:
    while True:
        try:
            Data.update_conversion_rates(output_currency, json_output_enabled)
            Lending.transfer_balances()
            Lending.cancel_all()
            Lending.lend_all()
            log.refreshStatus(Data.stringify_total_lended(*Data.get_total_lended()), Data.get_max_duration(
                end_date, "status"))
            log.persistStatus()
            sys.stdout.flush()
            time.sleep(Lending.get_sleep_time())
        except Exception as ex:
            log.log("ERROR: " + str(ex))
            log.persistStatus()
            print timestamp()
            print traceback.format_exc()
            if 'Invalid API key' in str(ex):
                print "!!! Troubleshooting !!!"
                print "Are your API keys correct? No quotation. Just plain keys."
                exit(1)
            if 'Nonce must be greater' in str(ex):
                print "!!! Troubleshooting !!!"
                print "Are you reusing the API key in multiple applications? use a unique key for every application."
                exit(1)
            if 'Permission denied' in str(ex):
                print "!!! Troubleshooting !!!"
                print "Are you using IP filter on the key? Maybe your IP changed?"
                exit(1)
            sys.stdout.flush()
            time.sleep(Lending.get_sleep_time())
            pass
except KeyboardInterrupt:
    if web_server_enabled:
        WebServer.stop_web_server()
    log.log('bye')
    exit(0)
