# coding=utf-8
from plugins.Plugin import Plugin
import sqlite3

DB_VERSION = 2
BITCOIN_GENESIS_BLOCK_DATE = "2009-01-03 18:15:05"
DB_DROP = "DROP TABLE IF EXISTS history"
DB_CREATE = "CREATE TABLE IF NOT EXISTS history(" \
            "id INTEGER NOT NULL, open TIMESTAMP, close TIMESTAMP," \
            " duration NUMBER, interest NUMBER, rate NUMBER," \
            " currency TEXT NOT NULL, amount NUMBER, earned NUMBER, fee NUMBER," \
            " UNIQUE(id, currency) ON CONFLICT REPLACE )"
DB_INSERT = "INSERT OR REPLACE INTO 'history'" \
            "('id','open','close','duration','interest','rate','currency','amount','earned','fee')" \
            " VALUES (?,?,?,?,?,?,?,?,?,?);"
DB_GET_LAST_TIMESTAMP = "SELECT max(close) as last_timestamp FROM 'history'"
DB_GET_FIRST_TIMESTAMP = "SELECT min(close) as first_timestamp FROM 'history'"
DB_GET_TOTAL_EARNED = "SELECT sum(earned) as total_earned, currency FROM 'history' GROUP BY currency"
DB_GET_YESTERDAY_EARNINGS = "SELECT sum(earned) as total_earned, currency FROM 'history' " \
                            "WHERE close BETWEEN datetime('now', 'start of day', '-1 day') " \
                            "AND datetime('now','start of day') GROUP BY currency"
DB_GET_TODAYS_EARNINGS = "SELECT sum(earned) as total_earned, currency FROM 'history' " \
                         "WHERE close > datetime('now','start of day') GROUP BY currency"


class AccountStats(Plugin):
    last_notification = 0
    earnings = {}
    report_interval = 86400

    def on_bot_init(self):
        super(AccountStats, self).on_bot_init()
        self.init_db()
        self.check_upgrade()
        self.report_interval = int(self.config.get("ACCOUNTSTATS", "ReportInterval", 86400))

    def before_lending(self):
        for coin in self.earnings:
            for key in self.earnings[coin]:
                self.log.updateStatusValue(coin, key, self.earnings[coin][key])

    def after_lending(self):
        if self.get_db_version() > 0 \
                and self.last_notification != 0 \
                and self.last_notification + self.report_interval > sqlite3.time.time():
            return
        self.update_history()
        self.notify_stats()

    # noinspection PyAttributeOutsideInit
    def init_db(self):
        self.db = sqlite3.connect('market_data/loan_history.sqlite3')
        self.db.execute(DB_CREATE)
        self.db.commit()

    def check_upgrade(self):
        if 0 < self.get_db_version() < DB_VERSION:
            # drop table and set version to 0 to reinitialize db to new version.
            self.db.execute(DB_DROP)
            self.set_db_version(0)
            self.db.commit()
            self.db.execute(DB_CREATE)
            self.db.commit()
            self.log.log('Upgraded AccountStats DB  to version ' + str(DB_VERSION))

    def update_history(self):
        # timestamps are in UTC
        last_time_stamp = self.get_last_timestamp()

        if last_time_stamp is None:
            # no entries means db is empty and needs initialization
            last_time_stamp = BITCOIN_GENESIS_BLOCK_DATE
            self.db.execute("PRAGMA user_version = 0")

        self.fetch_history(self.api.create_time_stamp(last_time_stamp), sqlite3.time.time())

        # Fetch history in batches, loop to make sure we got everything
        if (self.get_db_version() == 0) and (self.get_first_timestamp() is not None):
            last_time_stamp = BITCOIN_GENESIS_BLOCK_DATE
            loop = True
            while loop:
                sqlite3.time.sleep(10)  # delay a bit, try not to annoy exchange
                first_time_stamp = self.get_first_timestamp()
                count = self.fetch_history(self.api.create_time_stamp(last_time_stamp),
                                           self.api.create_time_stamp(first_time_stamp))
                loop = count != 0

            # if we reached here without errors means we managed to fetch all the history, db is ready.
            self.set_db_version(DB_VERSION)

    def set_db_version(self, version):
        self.db.execute("PRAGMA user_version = " + str(version))

    def get_db_version(self):
        return self.db.execute("PRAGMA user_version").fetchone()[0]

    def fetch_history(self, first_time_stamp, last_time_stamp):
        history = self.api.return_lending_history(first_time_stamp, last_time_stamp - 1, 5000)
        loans = []
        for loan in history:
            loans.append(
                [loan['id'], loan['open'], loan['close'], loan['duration'], loan['interest'],
                 loan['rate'], loan['currency'], loan['amount'], loan['earned'], loan['fee']])
        self.db.executemany(DB_INSERT, loans)
        self.db.commit()
        count = len(loans)
        self.log.log('Downloaded ' + str(count) + ' loans history '
                     + sqlite3.datetime.datetime.utcfromtimestamp(first_time_stamp).strftime('%Y-%m-%d %H:%M:%S')
                     + ' to ' + sqlite3.datetime.datetime.utcfromtimestamp(last_time_stamp - 1).strftime(
            '%Y-%m-%d %H:%M:%S'))
        if count > 0:
            self.log.log('Last: ' + history[0]['close'] + ' First:' + history[count - 1]['close'])
        return count

    def get_last_timestamp(self):
        cursor = self.db.execute(DB_GET_LAST_TIMESTAMP)
        row = cursor.fetchone()
        cursor.close()
        return row[0]

    def get_first_timestamp(self):
        cursor = self.db.execute(DB_GET_FIRST_TIMESTAMP)
        row = cursor.fetchone()
        cursor.close()
        return row[0]

    def notify_stats(self):
        if (self.get_db_version() == 0) and (self.get_first_timestamp() is not None):
            # only log an error if there are actually loans in DB
            self.log.log_error('AccountStats DB isn\'t ready.')
            return

        self.earnings = {}
        output = ''

        # Today's earnings
        cursor = self.db.execute(DB_GET_TODAYS_EARNINGS)
        row = cursor.fetchone()
        if row is not None:
            while row is not None:
                output += self.format_value(row[0]) + ' ' + str(row[1]) + ' Today\n'
                if row[1] not in self.earnings:
                    self.earnings[row[1]] = {}
                self.earnings[row[1]]['todayEarnings'] = row[0]
                row = cursor.fetchone()
        else:
            output += 'None Today\n'
        cursor.close()

        # Yesterday's earnings
        cursor = self.db.execute(DB_GET_YESTERDAY_EARNINGS)
        row = cursor.fetchone()
        if row is not None:
            while row is not None:
                output += self.format_value(row[0]) + ' ' + str(row[1]) + ' Yesterday\n'
                if row[1] not in self.earnings:
                    self.earnings[row[1]] = {}
                self.earnings[row[1]]['yesterdayEarnings'] = row[0]
                row = cursor.fetchone()
        else:
            output += 'None Yesterday\n'
        cursor.close()

        # Total Earnings
        cursor = self.db.execute(DB_GET_TOTAL_EARNED)
        row = cursor.fetchone()
        if row is not None:
            while row is not None:
                output += self.format_value(row[0]) + ' ' + str(row[1]) + ' in total\n'
                if row[1] not in self.earnings:
                    self.earnings[row[1]] = {}
                self.earnings[row[1]]['totalEarnings'] = row[0]
                row = cursor.fetchone()
        else:
            output += 'Unknown total earnings.\n'
        cursor.close()

        if output != '':
            self.last_notification = sqlite3.time.time()
            output = 'Earnings:\n----------\n' + output
            self.log.notify(output, self.notify_config)
            self.log.log(output)

    @staticmethod
    def format_value(value):
        return '{0:0.12f}'.format(float(value)).rstrip('0').rstrip('.')
