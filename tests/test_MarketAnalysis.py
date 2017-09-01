from hypothesis import given, settings
from hypothesis.strategies import floats, lists, integers
from hypothesis.extra.datetime import datetimes

import csv
import datetime
from pytz import timezone
import tempfile

# Hack to get relative imports - probably need to fix the dir structure instead but we need this at the minute for
# pytest to work
import os, sys, inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from modules.MarketAnalysis import MarketAnalysis
from modules.Configuration import FULL_LIST
from modules.Poloniex import Poloniex
import modules.Configuration as Config
import modules.Data as Data

Config.init('default.cfg', Data)
api = Poloniex(Config.get("API", "apikey", None), Config.get("API", "secret", None))
Data.init(api, None)
MA = MarketAnalysis(Config, api)


def create_dummy_rate_file(rate_file):
    rates = lists(floats(min_value=0.00001, allow_nan=False, allow_infinity=False), min_size=0, max_size=100).example()
    max_year = datetime.datetime.now().year
    date_times = lists(datetimes(min_year=2016, max_year=max_year), min_size=len(rates),
                       max_size=len(rates)).map(sorted).example()
    with open(rate_file, 'a') as f:
        for date_time, rate in zip(date_times, rates):
            writer = csv.writer(f, lineterminator='\n')
            market_data = [float(date_time.strftime("%s")), rate]
            writer.writerow(market_data)
    return rates, date_times


def add_test_files_to_MA_obj(MA_obj):
    test_rates = {}
    date_times = {}
    # TODO - These need deleted at the end of testing
    for cur in FULL_LIST:
        MA_obj.open_files[cur] = tempfile.NamedTemporaryFile(delete=False).name
        test_rates[cur], date_times[cur] = create_dummy_rate_file(MA_obj.open_files[cur])
    return test_rates, date_times


def test_get_rate_list():
    test_rates, _ = add_test_files_to_MA_obj(MA)
    for cur in FULL_LIST:
        rates = MA.get_rate_list(cur)
        assert rates == test_rates[cur]


@given(lists(floats(min_value=0.00001, allow_nan=False, allow_infinity=False)))
def test_get_rate_suggestion(rates):
    for cur in FULL_LIST:
        rate = MA.get_rate_suggestion(cur, method='percentile')
        assert(rate >= 0)

    for cur in FULL_LIST:
        rate = MA.get_rate_suggestion(cur, rates, 'percentile')
        assert(rate >= 0)


@given(lists(floats(min_value=0, allow_nan=False, allow_infinity=False), min_size=3, max_size=100),
       integers(min_value=1, max_value=99))
def test_get_percentile(rates, lending_style):
    np_perc = MA.get_percentile(rates, lending_style, True)
    math_perc = MA.get_percentile(rates, lending_style, False)
    assert(np_perc == math_perc)


def get_file_len(filename):
    i = -1
    with open(filename) as f:
        for i, _ in enumerate(f):
            pass
    return i + 1


def test_update_market():
    add_test_files_to_MA_obj(MA)
    file_lens = {}
    for cur in FULL_LIST:
        file_lens[cur] = get_file_len(MA.open_files[cur])
    for cur in FULL_LIST:
        MA.update_market(cur)
        assert(file_lens[cur] + 1 == get_file_len(MA.open_files[cur]))


@given(integers(min_value=0))
@settings(max_examples=50)
def test_delete_old_data(max_age):
    add_test_files_to_MA_obj(MA)
    MA.max_age = max_age
    for cur, rate_file in MA.open_files.items():
        MA.delete_old_data(cur)
        with open(rate_file) as f:
            reader = csv.reader(f)
            for row in reader:
                assert(MA.get_day_difference(row[0]) < max_age)
