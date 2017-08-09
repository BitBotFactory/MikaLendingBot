# coding=utf-8
from decimal import Decimal

coin_cfg = []
max_to_lend_rate = 0
max_to_lend = 0
max_percent_to_lend = 0
min_loan_size = 0.001
log = None


def init(config, log1):
    global coin_cfg, max_to_lend_rate, max_to_lend, max_percent_to_lend, min_loan_size, log
    coin_cfg = coin_cfg = config.get_coin_cfg()
    max_to_lend = Decimal(config.get('BOT', 'maxtolend', False, 0))
    max_percent_to_lend = Decimal(config.get('BOT', 'maxpercenttolend', False, 0, 100)) / 100
    max_to_lend_rate = Decimal(config.get('BOT', 'maxtolendrate', False, 0.003, 5)) / 100
    min_loan_size = Decimal(config.get("BOT", 'minloansize', None, 0.001))
    log = log1


def amount_to_lend(active_cur_test_balance, active_cur, lending_balance, low_rate):
    restrict_lend = False
    active_bal = Decimal(0)
    log_data = str("")
    cur_max_to_lend_rate = max_to_lend_rate
    cur_max_to_lend = max_to_lend
    cur_max_percent_to_lend = max_percent_to_lend
    if active_cur in coin_cfg:
        cur_max_to_lend_rate = coin_cfg[active_cur]['maxtolendrate']
        cur_max_to_lend = coin_cfg[active_cur]['maxtolend']
        cur_max_percent_to_lend = coin_cfg[active_cur]['maxpercenttolend']
    if cur_max_to_lend_rate == 0 and low_rate > 0 or cur_max_to_lend_rate >= low_rate > 0:
        log_data = ("The Lower Rate found on " + active_cur + " is " + str(
            "%.4f" % (Decimal(low_rate) * 100)) + "% vs conditional rate " + str(
            "%.4f" % (Decimal(cur_max_to_lend_rate) * 100)) + "%. ")
        restrict_lend = True
    if cur_max_to_lend != 0 and restrict_lend:
        log.updateStatusValue(active_cur, "maxToLend", cur_max_to_lend)
        if lending_balance > (active_cur_test_balance - cur_max_to_lend):
            active_bal = (lending_balance - (active_cur_test_balance - cur_max_to_lend))
    if cur_max_to_lend == 0 and cur_max_percent_to_lend != 0 and restrict_lend:
        log.updateStatusValue(active_cur, "maxToLend", (cur_max_percent_to_lend * active_cur_test_balance))
        if lending_balance > (active_cur_test_balance - (cur_max_percent_to_lend * active_cur_test_balance)):
            active_bal = (lending_balance - (active_cur_test_balance - (
                cur_max_percent_to_lend * active_cur_test_balance)))
    if cur_max_to_lend == 0 and cur_max_percent_to_lend == 0:
        log.updateStatusValue(active_cur, "maxToLend", active_cur_test_balance)
        active_bal = lending_balance
    if not restrict_lend:
        log.updateStatusValue(active_cur, "maxToLend", active_cur_test_balance)
        active_bal = lending_balance
    if (lending_balance - active_bal) < min_loan_size:
        active_bal = lending_balance
    if active_bal < lending_balance:
        log.log(log_data + " Lending " + str("%.8f" % Decimal(active_bal)) + " of " + str(
            "%.8f" % Decimal(lending_balance)) + " Available")
    return active_bal
