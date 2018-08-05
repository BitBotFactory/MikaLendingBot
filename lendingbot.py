# coding=utf-8
import argparse
import os
import sys
import time
import traceback
import socket
from decimal import Decimal
from http.client import BadStatusLine
from urllib.error import URLError

import modules.BotConfiguration
import libs.Data as Data
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
#parser.add_argument("-cfg", "--config", help="Location of custom configuration file, overrides settings below")
parser.add_argument("-dry", "--dryrun", help="Make pretend orders", action="store_true")
parser.add_argument("-up", "--update", help="Do a git pull, then start. (Needs git install)", action="store_true")
args = parser.parse_args()  # End args.

# Start handling args.
dry_run = bool(args.dryrun)
update = bool(args.update)
if update:
    print("Autoupdating...")
    import subprocess
    up_cmd = ["git", "pull"]
    try:
        up_out = subprocess.check_output(up_cmd).decode(sys.stdout.encoding)
    # except FileNotFoundError:
    #    up_out = "command not found"
    except Exception:
        print("Looks like you need to use sudo...")
        up_cmd.insert(0, "sudo")
        up_cmd.insert(1, "--non-interactive")
        up_out = subprocess.check_output(up_cmd).decode(sys.stdout.encoding)
    if "Already" in up_out:
        print("No update available.")
    elif "Updating" in up_out:
        print("Update downloaded.")
    elif "tracking" in up_out:
        print("There is something wrong with your git branch settings.\n"
              "Do (sudo) git checkout master!\n"
              "Error:\n" + up_out)
    elif "command not found" in up_out:
        print("You do not have git installed!")
    elif "a git repository" in up_out:
        print("You did not install the bot using git!\n"
              "Reinstall using git using:\n"
              "(sudo) git clone http://github.com/BitBotFactory/poloniexlendingbot.git")
    elif "Permission denied" in up_out:
        print("Your sudo is not configured for non-interactive usage, this is necessary.")
    else:
        print(up_out)
    cmd = ["python", "lendingbot.py"]
    if args.config:
        cmd.append("--config")
        cmd.append(args.config)
    if args.dryrun:
        cmd.append("--dryrun")
    print("Done, starting bot...\n")
    subprocess.call(cmd)
    exit(0)

# if args.config:
#    config_location = args.config
# else:
#    config_location = '/settings/default.cfg'
# End handling args.

# Config format: Config.get(category, option, default_value=False, lower_limit=False, upper_limit=False)
# A default_value "None" means that the option is required and the bot will not run without it.
# Do not use lower or upper limit on any config options which are not numbers.
# Define the variable from the option in the module where you use it.

mypath = os.curdir + "/settings"
worker_settings = ["/settings/" + f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
if '/settings/master.cfg' in worker_settings:
    worker_settings.remove('/settings/master.cfg')
    pass
else:
    print("Cannot find master config.")
    exit(1)
config_location = worker_settings[0]
Config = modules.BotConfiguration.BotConfig(config_location)
output_currency = Config.get('BOT', 'outputCurrency', 'BTC')
end_date = Config.get('BOT', 'endDate')
exchange = Config.get_exchange()

json_output_enabled = Config.has_option('BOT', 'jsonfile') and Config.has_option('BOT', 'jsonlogsize')
jsonfile = Config.get('BOT', 'jsonfile', '')

# Configure web server
web_server_enabled = Config.getboolean('BOT', 'startWebServer')
if web_server_enabled:
    if json_output_enabled is False:
        # User wants webserver enabled. Must have JSON enabled. Force logging with defaults.
        json_output_enabled = True
        jsonfile = Config.get('BOT', 'jsonfile', 'www/botlog.json')

    import modules.WebServer as WebServer
    WebServer.initialize_web_server(Config)

# Configure logging
log = Logger(jsonfile, Decimal(Config.get('BOT', 'jsonlogsize', 200)), exchange)

# initialize the remaining stuff
api = ExchangeApiFactory.createApi(exchange, Config, log)
MaxToLend.init(Config, log)
notify_conf = Config.get_notification_config()
if Config.has_option('MarketAnalysis', 'analyseCurrencies'):
    from modules.MarketAnalysis import MarketAnalysis
    # Analysis.init(Config, api, Data)
    analysis = MarketAnalysis(Config, api)
    analysis.run()
else:
    analysis = None
Lending.init(Config, api, log, Data, MaxToLend, dry_run, analysis, notify_conf)

# load plugins
PluginsManager.init(Config, api, log, notify_conf)
# Start dns cache managing
prv_getaddrinfo = socket.getaddrinfo
dns_cache = {}  # or a weakref.WeakValueDictionary()


def new_getaddrinfo(*urlargs):
    """Overloads the default socket dns resolution to have a cache,
    resets at the beginning of each loop.
    https://stackoverflow.com/questions/2236498/tell-urllib2-to-use-custom-dns"""
    try:
        return dns_cache[urlargs]
    except KeyError:
        res = prv_getaddrinfo(*urlargs)
        dns_cache[urlargs] = res
        return res


socket.getaddrinfo = new_getaddrinfo

# TODO: build workers

print(worker_settings)
