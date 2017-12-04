# coding=utf-8
import json
import os
from ConfigParser import SafeConfigParser
from decimal import Decimal

config = SafeConfigParser()
# This module is the middleman between the bot and a SafeConfigParser object, so that we can add extra functionality
# without clogging up lendingbot.py with all the config logic. For example, added a default value to get().


class Config(object):
    def __init__(self, file_location, data=None):
        self.file_location = file_location
        self.data = data
        loaded_files = config.read(file_location)
        if len(loaded_files) != 1:
            self.create_default_config_file()
        self.api = self.api_configs()
        self.bot = self.bot_configs()

    def api_configs(self):
        cfg = {}
        cfg['exchange'] = self.get_exchange()
        if cfg['exchange'].lower() == 'poloniex':
            cfg['exchangeMaxRate'] = 5
            cfg['exchangeMaxDays'] = 60
        elif cfg['exchange'].lower() == 'bitfinex':
            cfg['exchMaxRate'] = 99
            cfg['exchangeMaxDays'] = 30
        return cfg

    def bot_configs(self):
        cfg = {}
        cfg['label'] = self.get("BOT", "label", "Lending Bot")
        cfg['sleeptimeactive'] = float(self.get("BOT", "sleeptimeactive", None, 1, 3600))
        cfg['sleeptimeinactive'] = float(self.get("BOT", "sleeptimeinactive", None, 1, 3600))
        cfg['timeout'] = int(self.get("BOT", "timeout", 30, 1, 180))
        cfg['mindailyrate'] = Decimal(self.get("BOT", "mindailyrate", None, 0.003, self.api['exchangeMaxRate'])) / 100
        cfg['maxdailyrate'] = Decimal(self.get("BOT", "maxdailyrate", None, 0.003, self.api['exchangeMaxRate'])) / 100
        cfg['spreadlend'] = int(self.get("BOT", "spreadlend", None, 1, 20))
        cfg['gapmode'] = self.get('BOT', 'gapmode', False).lower().strip(" ")
        cfg['gapbottom'] = Decimal(self.get("BOT", "gapbottom", None, 0))
        cfg['gaptop'] = Decimal(self.get("BOT", "gaptop", None, cfg['gapbottom']))
        cfg['xdaythreshold'] = float(self.get("BOT", "xdaythreshold", None, 0.003, 5)) / 100
        cfg['xdays'] = str(self.get("BOT", "xdays", None, 2, self.api['exchangeMaxDays']))
        cfg['xday_spread'] = float(self.get('BOT', 'xdayspread', 0, 0, 10))
        cfg['transferableCurrencies'] = self.get_currencies_list('transferableCurrencies')
        cfg['minloansize'] = Decimal(self.get("BOT", 'minloansize', None, 0.001))
        cfg['keepstuckorders'] = self.getboolean('BOT', "keepstuckorders", True)
        cfg['hideCoins'] = self.getboolean('BOT', 'hideCoins', True)
        cfg['end_date'] = self.get('BOT', 'endDate')
        cfg['maxtolend'] = Decimal(self.get('BOT', 'maxtolend', False, 0))
        cfg['maxpercenttolend'] = Decimal(self.get('BOT', 'maxpercenttolend', False, 0, 100)) / 100
        cfg['maxtolendrate'] = Decimal(self.get('BOT', 'maxtolendrate', False, 0.003, 5)) / 100
        cfg['maxtolendrate'] = Decimal(self.get('BOT', 'maxtolendrate', False, 0.003, 5)) / 100
        cfg['jsonfile'] = self.get('BOT', 'jsonfile', 'www/botlog.json')
        cfg['jsonlogsize'] = int(self.get('BOT', 'jsonlogsize', 200))
        cfg['json_output_enabled'] = self.has_option('BOT', 'jsonfile') and self.has_option('BOT', 'jsonlogsize')
        cfg['web_server_enabled'] = self.getboolean('BOT', 'startWebServer')
        cfg['outputCurrency'] = self.get('BOT', 'outputCurrency', 'BTC')
        return cfg
        cfg['analyseCurrencies'] = self.get('MarketAnalysis', 'analyseCurrencies', False)
        cfg['ma_debug_log'] = self.getboolean('MarketAnalysis', 'ma_debug_log')
        cfg['notify_conf'] = self.get_notification_config()

    def create_default_config_file(self):
        import shutil
        # Copy default config file if not found
        try:
            shutil.copy('default.cfg.example', self.file_location)
            print '\ndefault.cfg.example has been copied to ' + self.file_location + '\n' \
                  'Edit it with your API key and custom settings.\n'
            raw_input("Press Enter to acknowledge and exit...")
            exit(1)
        except Exception as ex:
            ex.message = ex.message if ex.message else str(ex)
            print("Failed to automatically copy config. Please do so manually. Error: {0}".format(ex.message))
            exit(1)

    def has_option(self, category, option):
        try:
            return True if os.environ["{0}_{1}".format(category, option)] else _
        except (KeyError, NameError):  # KeyError for no env var, NameError for _ (empty var) and then to continue
            return config.has_option(category, option)

    def getboolean(self, category, option, default_value=False):
        if self.has_option(category, option):
            try:
                return bool(os.environ["{0}_{1}".format(category, option)])
            except KeyError:
                return config.getboolean(category, option)
        else:
            return default_value

    def get(self, category, option, default_value=False, lower_limit=False, upper_limit=False):
        if self.has_option(category, option):
            try:
                value = os.environ["{0}_{1}".format(category, option)]
            except KeyError:
                value = config.get(category, option)
            try:
                if lower_limit and float(value) < float(lower_limit):
                    print "WARN: [%s]-%s's value: '%s' is below the minimum limit: %s, which will be used instead." % \
                          (category, option, value, lower_limit)
                    value = lower_limit
                if upper_limit and float(value) > float(upper_limit):
                    print "WARN: [%s]-%s's value: '%s' is above the maximum limit: %s, which will be used instead." % \
                          (category, option, value, upper_limit)
                    value = upper_limit
                return value
            except ValueError:
                if default_value is None:
                    print "ERROR: [%s]-%s is not allowed to be left empty. Please check your config." % (category, option)
                    exit(1)
                return default_value
        else:
            if default_value is None:
                print "ERROR: [%s]-%s is not allowed to be left unset. Please check your config." % (category, option)
                exit(1)
            return default_value

    # Below: functions for returning some config values that require special treatment.

    def get_exchange(self):
        '''
        Returns used exchange
        '''
        try:
            return os.environ['API_exchange'].upper()
        except KeyError:
            return self.get('API', 'exchange', 'Poloniex').upper()

    def get_coin_cfg(self):
        coin_cfg = {}
        if config.has_option("BOT", "coinconfig"):
            try:
                coin_config = (json.loads(config.get("BOT", "coinconfig")))
                for cur in coin_config:
                    cur = cur.split(':')
                    coin_cfg[cur[0]] = dict(minrate=(Decimal(cur[1])) / 100, maxactive=Decimal(cur[2]),
                                            maxtolend=Decimal(cur[3]), maxpercenttolend=(Decimal(cur[4])) / 100,
                                            maxtolendrate=(Decimal(cur[5])) / 100)
            except Exception as ex:
                ex.message = ex.message if ex.message else str(ex)
                print("Coinconfig parsed incorrectly, please refer to the documentation. Error: {0}".format(ex.message))
        else:
            for cur in self.get_all_currencies():
                if config.has_section(cur):
                    try:
                        coin_cfg[cur] = {}
                        coin_cfg[cur]['minrate'] = (Decimal(config.get(cur, 'mindailyrate'))) / 100
                        coin_cfg[cur]['maxactive'] = Decimal(config.get(cur, 'maxactiveamount'))
                        coin_cfg[cur]['maxtolend'] = Decimal(config.get(cur, 'maxtolend'))
                        coin_cfg[cur]['maxpercenttolend'] = (Decimal(config.get(cur, 'maxpercenttolend'))) / 100
                        coin_cfg[cur]['maxtolendrate'] = (Decimal(config.get(cur, 'maxtolendrate'))) / 100
                        coin_cfg[cur]['gapmode'] = self.get_gap_mode(cur, 'gapmode')
                        coin_cfg[cur]['gapbottom'] = Decimal(self.get(cur, 'gapbottom', False, 0))
                        coin_cfg[cur]['gaptop'] = Decimal(self.get(cur, 'gaptop', False, coin_cfg[cur]['gapbottom']))

                    except Exception as ex:
                        ex.message = ex.message if ex.message else str(ex)
                        print("Coinconfig for " + cur + " parsed incorrectly, please refer to the documentation. "
                              "Error: {0}".format(ex.message))
                        # Need to raise this exception otherwise the bot will continue if you config one cur correctly
                        raise
        return coin_cfg

    def get_min_loan_sizes(self):
        min_loan_sizes = {}
        for cur in self.get_all_currencies():
            if config.has_section(cur):
                try:
                    min_loan_sizes[cur] = Decimal(self.get(cur, 'minloansize', lower_limit=0.01))
                except Exception as ex:
                    ex.message = ex.message if ex.message else str(ex)
                    print("minloansize for " + cur + " parsed incorrectly, please refer to the documentation. "
                          "Error: {0}".format(ex.message))
                    # Bomb out if something isn't configured correctly
                    raise
        return min_loan_sizes

    def get_currencies_list(self, option, section='BOT'):
        if config.has_option(section, option):
            full_list = self.get_all_currencies()
            cur_list = []
            raw_cur_list = config.get(section, option).split(",")
            for raw_cur in raw_cur_list:
                cur = raw_cur.strip(' ').upper()
                if cur == 'ALL':
                    return full_list
                elif cur == 'ACTIVE':
                    cur_list += self.data.get_lending_currencies()
                else:
                    if cur in full_list:
                        cur_list.append(cur)
            return list(set(cur_list))
        else:
            return []

    def get_gap_mode(self, category, option):
        if config.has_option(category, option):
            full_list = ['raw', 'rawbtc', 'relative']
            value = self.get(category, 'gapmode', False).lower().strip(" ")
            if value not in full_list:
                print "ERROR: Invalid entry '%s' for [%s]-gapMode. Please check your config. Allowed values are: %s" % \
                      (value, category, ", ".join(full_list))
                exit(1)
            return value.lower()
        else:
            return False

    def get_all_currencies(self):
        '''
        Get list of all supported currencies by exchange
        '''
        exchange = self.get_exchange()
        if config.has_option(exchange, 'all_currencies'):
            cur_list = []
            raw_cur_list = config.get(exchange, 'all_currencies').split(',')
            for raw_cur in raw_cur_list:
                cur = raw_cur.strip(' ').upper()
                if (cur[0] != "#"):		# Blacklisting: E.g. ETH, #BTG, QTUM
                    cur_list.append(cur)
            return cur_list
        elif exchange == 'POLONIEX':
            # default, compatibility to old 'Poloniex only' config
            return ['STR', 'BTC', 'BTS', 'CLAM', 'DOGE', 'DASH', 'LTC', 'MAID', 'XMR', 'XRP', 'ETH', 'FCT']
        else:
            raise Exception('ERROR: List of supported currencies must defined in [' + exchange + '] all_currencies.')

    def get_notification_config(self):
        notify_conf = {'enable_notifications': config.has_section('notifications')}

        # For boolean parameters
        for conf in ['notify_tx_coins',
                     'notify_xday_threshold',
                     'notify_new_loans',
                     'notify_caught_exception',
                     'email',
                     'slack',
                     'telegram',
                     'pushbullet',
                     'irc']:
            notify_conf[conf] = self.getboolean('notifications', conf)

        # For string-based parameters
        for conf in ['notify_prefix']:
            _val = self.get('notifications', conf, '').strip()
            if len(_val) > 0:
                notify_conf[conf] = _val

        # in order not to break current config, parsing for False
        notify_summary_minutes = self.get('notifications', 'notify_summary_minutes')
        notify_conf['notify_summary_minutes'] = 0 if notify_summary_minutes == 'False' else int(notify_summary_minutes)

        if notify_conf['email']:
            for conf in ['email_login_address', 'email_login_password', 'email_smtp_server', 'email_smtp_port',
                         'email_to_addresses', 'email_smtp_starttls']:
                notify_conf[conf] = self.get('notifications', conf)
            notify_conf['email_to_addresses'] = notify_conf['email_to_addresses'].split(',')

        if notify_conf['slack']:
            for conf in ['slack_token', 'slack_channels', 'slack_username']:
                notify_conf[conf] = self.get('notifications', conf)
            notify_conf['slack_channels'] = notify_conf['slack_channels'].split(',')
            if not notify_conf['slack_username']:
                notify_conf['slack_username'] = 'Slack API Tester'

        if notify_conf['telegram']:
            for conf in ['telegram_bot_id', 'telegram_chat_ids']:
                notify_conf[conf] = self.get('notifications', conf)
            notify_conf['telegram_chat_ids'] = notify_conf['telegram_chat_ids'].split(',')

        if notify_conf['pushbullet']:
            for conf in ['pushbullet_token', 'pushbullet_deviceid']:
                notify_conf[conf] = self.get('notifications', conf)

        if notify_conf['irc']:
            for conf in ['irc_host', 'irc_port', 'irc_nick', 'irc_ident', 'irc_realname', 'irc_target']:
                notify_conf[conf] = self.get('notifications', conf)
            notify_conf['irc_port'] = int(notify_conf['irc_port'])
            notify_conf['irc_debug'] = self.getboolean('notifications', 'irc_debug')

        return notify_conf

    def get_plugins_config(self):
        active_plugins = []
        if self.has_option("BOT", "plugins"):
            active_plugins = map(str.strip, self.get("BOT", "plugins").split(','))
        return active_plugins
