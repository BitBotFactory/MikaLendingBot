import csv
import threading
import time
import datetime
from cStringIO import StringIO
try:
    import numpy
    use_numpy = True
except ImportError as ex:
    ex.message = ex.message if ex.message else str(ex)
    print("WARN: Module Numpy not found, using manual percentile method instead. "
          "It is recommended to install Numpy. Error: {0}".format(ex.message))
    use_numpy = False

currencies_to_analyse = []
open_files = {}
max_age = 0
update_interval = 0
api = None
Data = None
lending_style = 0


def init(config, api1, data1):
    global currencies_to_analyse, open_files, max_age, update_interval, api, Data, lending_style
    currencies_to_analyse = config.get_currencies_list('analyseCurrencies')
    max_age = int(config.get('BOT', 'analyseMaxAge', 30, 1, 365))
    update_interval = int(config.get('BOT', 'analyseUpdateInterval', 60, 10, 3600))
    lending_style = int(config.get('BOT', 'lendingStyle', 50, 1, 99))
    api = api1
    Data = data1
    if len(currencies_to_analyse) != 0:
        for currency in currencies_to_analyse:

            try:
                api.api_query("returnLoanOrders", {'currency': currency, 'limit': '5'})
            except Exception as cur_ex:
                print "Error: You entered an incorrect currency: '" + currency + \
                      "' to analyse the market of, please check your settings. Error message: " + str(cur_ex)
                exit(1)

            else:
                path = "market_data/" + currency + "_market_data.csv"
                open_files[currency] = path

        thread = threading.Thread(target=update_market_loop)
        thread.deamon = True
        thread.start()


def update_market_loop():
    while True:
        try:
            update_markets()
            delete_old_data()
        except Exception as ex:
            ex.message = ex.message if ex.message else str(ex)
            print("Error in MarketAnalysis: {0}".format(ex.message))
        time.sleep(update_interval)


def update_markets():
    for cur in open_files:
        with open(open_files[cur], 'a') as f:
            writer = csv.writer(f, lineterminator='\n')
            raw_data = api.return_loan_orders(cur, 5)['offers'][0]
            market_data = [Data.timestamp(), raw_data['rate']]
            writer.writerow(market_data)


def delete_old_data():
    for cur in open_files:
        with open(open_files[cur], 'rb') as file_a:
            new_a_buf = StringIO()
            writer = csv.writer(new_a_buf)
            reader2 = csv.reader(file_a)
            for row in reader2:
                if get_day_difference(row[0]) < max_age:
                    writer.writerow(row)

        # At this point, the contents (new_a_buf) exist in memory
        with open(open_files[cur], 'wb') as file_b:
            file_b.write(new_a_buf.getvalue())


def get_day_difference(date_time):  # Will be in format '%Y-%m-%d %H:%M:%S'
    date1 = datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
    now = datetime.datetime.now()
    diff_days = (now - date1).days
    return diff_days


def get_rate_list(cur='all'):
    if cur == 'all':
        all_rates = {}
        for cur in open_files:
            with open(open_files[cur], 'r') as f:
                reader = csv.reader(f)
                rates = []
                for row in reader:
                    rates.append(row[1])
                rates = map(float, rates)
                all_rates[cur] = rates
        return all_rates

    else:
        if cur not in open_files:
            return []
        with open(open_files[cur], 'r') as f:
            reader = csv.reader(f)
            rates = []
            for row in reader:
                rates.append(row[1])
            rates = map(float, rates)
        return rates


def get_rate_suggestion(cur):
    if cur not in open_files:
        return 0
    try:
        rates = get_rate_list(cur)
        if use_numpy:
            result = numpy.percentile(rates, int(lending_style))
        else:
            rates.sort()
            index = int(lending_style * len(rates) / 100.0)
            result = rates[index]
        result = Data.truncate(result, 6)
        return result
    except Exception as exc:
        print "WARN: Exception found when analysing markets, if this happens for more than a couple minutes please " \
              "make a Github issue so we can fix it. Otherwise, you can safely ignore it. Error: " + str(exc)
        return 0
