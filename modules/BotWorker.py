# coding=utf-8
from modules.BotConfiguration import BotConfig


class BotWorker:
    def __init__(self, configname):
        global Config
        Config = BotConfig("/settings/" + configname)
        # do stuff with config pls
        return

    def run(self):
        print(f"Welcome to {Config.get('BOT', 'label', 'Lending Bot')} on {exchange}")

        try:
            while True:
                try:
                    super.dns_cache = {}  # Flush DNS Cache
                    Data.update_conversion_rates(output_currency, json_output_enabled, api, log)
                    PluginsManager.before_lending()
                    Lending.transfer_balances()
                    Lending.cancel_all()
                    Lending.lend_all()
                    PluginsManager.after_lending()
                    log.refreshStatus(Data.stringify_total_lent(*Data.get_total_lent(api)),
                                      Data.get_max_duration(end_date, "status"))
                    log.persistStatus()
                    sys.stdout.flush()
                    time.sleep(Lending.get_sleep_time())
                except KeyboardInterrupt:
                    # allow existing the main bot loop
                    raise
                except Exception as ex:
                    if not hasattr(ex, 'message'):
                        ex.message = str(ex)
                    log.log_error(ex.message)
                    log.persistStatus()
                    if 'Invalid API key' in ex.message:
                        print("!!! Troubleshooting !!!")
                        print("Are your API keys correct? No quotation. Just plain keys.")
                        exit(1)
                    elif 'Nonce must be greater' in ex.message:
                        print("!!! Troubleshooting !!!")
                        print(
                            "Are you reusing the API key in multiple applications? Use a unique key for every application.")
                        exit(1)
                    elif 'Permission denied' in ex.message:
                        print("!!! Troubleshooting !!!")
                        print("Are you using IP filter on the key? Maybe your IP changed?")
                        exit(1)
                    elif 'timed out' in ex.message:
                        print(f"Timed out, will retry in {Lending.get_sleep_time()} sec")
                    elif isinstance(ex, BadStatusLine):
                        print("Caught BadStatusLine exception from Poloniex, ignoring.")
                    elif 'Error 429' in ex.message:
                        additional_sleep = max(130.0 - Lending.get_sleep_time(), 0)
                        sum_sleep = additional_sleep + Lending.get_sleep_time()
                        log.log_error('IP has been banned due to many requests. Sleeping for {} seconds'.format(sum_sleep))
                        if Config.has_option('MarketAnalysis', 'analyseCurrencies'):
                            if api.req_period <= api.default_req_period * 1.5:
                                api.req_period += 3
                            if Config.getboolean('MarketAnalysis', 'ma_debug_log'):
                                print(
                                    f"Caught ERR_RATE_LIMIT, sleep capture & increase request wait. Current {api.req_period}")
                                log.log_error(
                                    'Expect this 130s ban periodically when using MarketAnalysis, it will fix itself')
                        time.sleep(additional_sleep)
                    # Ignore all 5xx errors (server error) as we can't do anything about it (https://httpstatuses.com/)
                    elif isinstance(ex, URLError):
                        print(f"Caught {ex.message} from exchange, ignoring.")
                    elif isinstance(ex, ApiError):
                        print(f"Caught {ex.message} reading from exchange API, ignoring.")
                    else:
                        print(traceback.format_exc())
                        version = Data.get_bot_version()  # throws error when put inside string
                        print(f"v{version} Unhandled error, please open a Github issue so we can fix it!")
                        if notify_conf['notify_caught_exception']:
                            log.notify(f"{ex}\n-------\n{traceback.format_exc()}", notify_conf)
                    sys.stdout.flush()
                    time.sleep(Lending.get_sleep_time())


        except KeyboardInterrupt:
            if web_server_enabled:
                WebServer.stop_web_server()
            PluginsManager.on_bot_exit()
            log.log("bye")
            print("bye")
            os._exit(0)  # Ad-hoc solution in place of 'exit(0)' TODO: Find out why non-daemon thread(s) are hanging on exit


