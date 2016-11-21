# coding=utf-8
from ConfigParser import SafeConfigParser

config = SafeConfigParser()
# This module is the middleman between the bot and a SafeConfigParser object, so that we can add extra functionality
# without clogging up lendingbot.py with all the config logic. For example, added a default value to get().


def init(file_location):
    loaded_files = config.read(file_location)
    if len(loaded_files) != 1:
        import shutil
        # Copy default config file if not found
        shutil.copy('default.cfg.example', 'default.cfg')
        print '\ndefault.cfg.example has been copied to default.cfg\n' \
              'Edit it with your API key and custom settings.\n'
        raw_input("Press Enter to acknowledge and exit...")
        exit(1)
    return config


def has_option(category, option):
    return config.has_option(category, option)


def getboolean(category, option):
    return config.getboolean(category, option)


def get(category, option, default_value=False, lower_limit=False, upper_limit=False):
    if config.has_option(category, option):
        value = config.get(category, option)
        if lower_limit:
            if float(value) < float(lower_limit):
                print "ERROR: " + option + "'s value: '" + value + "' is below the minimum limit: " + str(lower_limit)
                exit(1)
        if upper_limit:
            if float(value) > float(upper_limit):
                print "ERROR: " + option + "'s value: '" + value + "' is above the maximum limit: " + str(upper_limit)
                exit(1)
        return value
    else:
        if default_value is None:
            print "ERROR: " + option + " is not allowed to be left unset. Please check your config."
            exit(1)
        return default_value
# Below: functions for returning some config values that require special treatment.


def get_coin_cfg():
    coin_cfg = {}
    if config.has_option("BOT", "coinconfig"):
        try:
            # parsed
            import json
            from decimal import Decimal

            coin_config = (json.loads(config.get("BOT", "coinconfig")))
            for cur in coin_config:
                cur = cur.split(':')
                coin_cfg[cur[0]] = dict(minrate=(Decimal(cur[1])) / 100, maxactive=Decimal(cur[2]),
                                        maxtolent=Decimal(cur[3]), maxpercenttolent=(Decimal(cur[4])) / 100,
                                        maxtolentrate=(Decimal(cur[5])) / 100)
        except Exception as ex:
            print "Coinconfig parsed incorrectly, please refer to the documentation. Error: " + str(ex)
    return coin_cfg


def get_transferable_currencies():
    if config.has_option("BOT", "transferableCurrencies"):
        return (config.get("BOT", "transferableCurrencies")).split(",")
    else:
        return []
