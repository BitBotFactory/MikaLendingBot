from hypothesis import given, settings
from hypothesis.strategies import floats, lists, integers
from hypothesis.extra.datetime import datetimes

import csv
import datetime
import time
import pytest
import sqlite3 as sqlite
from random import randint
import pandas as pd

# Hack to get relative imports - probably need to fix the dir structure instead but we need this at the minute for
# pytest to work
import os, sys, inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from modules.MarketAnalysis import MarketAnalysis
from modules.Configuration import get_all_currencies
from modules.Poloniex import Poloniex
import modules.Configuration as Config
import modules.Data as Data

Config.init('default.cfg', Data)
api = Poloniex(Config, None)
Data.init(api, None)
MA = MarketAnalysis(Config, api)


def new_db():
    db_con = MA.create_connection(None, ':memory:')
    MA.create_rate_table(db_con, 3)
    return db_con


def random_rates():
    return lists(floats(min_value=0.00001, max_value=100, allow_nan=False, allow_infinity=False), min_size=0, max_size=100).example()


def random_dates(min_len, max_len):
    max_year = datetime.datetime.now().year
    return lists(datetimes(min_year=2016, max_year=max_year), min_size=min_len, max_size=max_len).map(sorted).example()


@pytest.fixture
def populated_db():
    price_levels = 3
    db_con = new_db()
    rates = random_rates()
    inserted_rates = []
    for rate in rates:
        market_data = []
        for level in range(price_levels):
            market_data.append("{0:.8f}".format(rate))
            market_data.append("{0:.2f}".format(rate))
        percentile = "{0:.8f}".format(rate)
        market_data.append(percentile)
        MA.insert_into_db(db_con, market_data)
        market_data = [float(x) for x in market_data]
        inserted_rates.append(market_data)
    return db_con, inserted_rates


def test_new_db():
    assert(isinstance(new_db(), sqlite.Connection))


def test_insert_into_db(populated_db):
    db_con, rates = populated_db
    query = "SELECT rate0, amnt0, rate1, amnt1, rate2, amnt2, percentile FROM loans;"
    db_rates = db_con.cursor().execute(query).fetchall()
    assert(len(rates) == len(db_rates))
    for db_rate, rate in zip(db_rates, rates):
        assert(len(rate) == len(db_rate))
        assert(len(rate) > 1)
        for level in range(len(rate)):
            assert(db_rate[level] == float(rate[level]))


def test_get_rates_from_db(populated_db):
    db_con, rates = populated_db
    db_rates = MA.get_rates_from_db(db_con, from_date=time.time() - 10, price_levels=['rate0'])
    for db_rate, rate in zip(db_rates, rates):
        assert(len(db_rate) == 2)
        assert(db_rate[1] == float(rate[0]))


def test_get_rate_list(populated_db):
    db_con, rates = populated_db
    db_rates = MA.get_rate_list(db_con, 1)
    assert(len(db_rates) == 1)


def test_get_rate_suggestion(populated_db):
    db_con, rates = populated_db
    MA = MarketAnalysis(Config, api)
    MA.data_tolerance = 1

    rate_db = MA.get_rate_suggestion(db_con, method='percentile')
    assert(rate_db >= 0)

    df = pd.DataFrame(rates)
    df.columns = ['rate0', 'a0', 'r1', 'a1', 'r2', 'a2', 'p']
    df.time = [time.time()] * len(df)
    rate_args = MA.get_rate_suggestion(db_con, df, 'percentile')
    assert(rate_args >= 0)

    rate = MA.get_rate_suggestion(db_con, method='MACD')
    assert(rate >= 0)


@given(lists(floats(min_value=0, allow_nan=False, allow_infinity=False), min_size=3, max_size=100),
       integers(min_value=1, max_value=99))
def test_get_percentile(rates, lending_style):
    np_perc = MA.get_percentile(rates, lending_style, use_numpy=True)
    math_perc = MA.get_percentile(rates, lending_style, use_numpy=False)
    assert(np_perc == math_perc)
