# coding=utf-8
import atexit
import datetime
import io
import json
import sys
import time

import ConsoleUtils
from RingBuffer import RingBuffer
from Notify import send_notification


class ConsoleOutput(object):
    def __init__(self):
        self._status = ''
        atexit.register(self._exit)

    def _exit(self):
        self._status += '  '  # In case the shell added a ^C
        self.status('')

    def status(self, msg, time='', days_remaining_msg=''):
        status = str(msg)
        cols = ConsoleUtils.get_terminal_size()[0]
        if msg != '' and len(status) > cols:
            # truncate status, try preventing console bloating
            status = str(msg)[:cols - 4] + '...'
        update = '\r'
        update += status
        update += ' ' * (len(self._status) - len(status))
        update += '\b' * (len(self._status) - len(status))
        sys.stderr.write(update)
        self._status = status

    def printline(self, line):
        update = '\r'
        update += line + ' ' * (len(self._status) - len(line)) + '\n'
        update += self._status
        sys.stderr.write(update)


class JsonOutput(object):
    def __init__(self, file, logLimit):
        self.jsonOutputFile = file
        self.jsonOutput = {}
        self.clearStatusValues()
        self.jsonOutputLog = RingBuffer(logLimit)

    def status(self, status, time, days_remaining_msg):
        self.jsonOutput["last_update"] = time + days_remaining_msg
        self.jsonOutput["last_status"] = status

    def printline(self, line):
        self.jsonOutputLog.append(line)

    def writeJsonFile(self):
        with io.open(self.jsonOutputFile, 'w', encoding='utf-8') as f:
            self.jsonOutput["log"] = self.jsonOutputLog.get()
            f.write(unicode(json.dumps(self.jsonOutput, ensure_ascii=False, sort_keys=True)))
            f.close()

    def statusValue(self, coin, key, value):
        if coin not in self.jsonOutputCoins:
            self.jsonOutputCoins[coin] = {}
        self.jsonOutputCoins[coin][key] = str(value)

    def clearStatusValues(self):
        self.jsonOutputCoins = {}
        self.jsonOutput["raw_data"] = self.jsonOutputCoins
        self.jsonOutputCurrency = {}
        self.jsonOutput["outputCurrency"] = self.jsonOutputCurrency

    def outputCurrency(self, key, value):
        self.jsonOutputCurrency[key] = str(value)


class Logger(object):
    def __init__(self, json_file='', json_log_size=-1):
        self._lent = ''
        self._daysRemaining = ''
        if json_file != '' and json_log_size != -1:
            self.output = JsonOutput(json_file, json_log_size)
        else:
            self.output = ConsoleOutput()
        self.refreshStatus()

    def timestamp(self):
        ts = time.time()
        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    def log(self, msg):
        self.output.printline(self.timestamp() + ' ' + msg)
        self.refreshStatus()

    def log_error(self, msg):
        log_message = self.timestamp() + ' Error: ' + msg
        self.output.printline(log_message)
        if type(self.output) is JsonOutput:
            print log_message
        self.refreshStatus()

    def offer(self, amt, cur, rate, days, msg):
        line = self.timestamp() + ' Placing ' + str(amt) + ' ' + str(cur) + ' at ' + str(
            float(rate) * 100) + '% for ' + days + ' days... ' + self.digestApiMsg(msg)
        self.output.printline(line)
        self.refreshStatus()

    def cancelOrders(self, cur, msg):
        line = self.timestamp() + ' Canceling all ' + str(cur) + ' orders... ' + self.digestApiMsg(msg)
        self.output.printline(line)
        self.refreshStatus()

    def refreshStatus(self, lent='', days_remaining=''):
        if lent != '':
            self._lent = lent
        if days_remaining != '':
            self._daysRemaining = days_remaining
        self.output.status(self._lent, self.timestamp(), self._daysRemaining)

    def updateStatusValue(self, coin, key, value):
        if hasattr(self.output, 'statusValue'):
            self.output.statusValue(coin, key, value)

    def updateOutputCurrency(self, key, value):
        if hasattr(self.output, 'outputCurrency'):
            self.output.outputCurrency(key, value)

    def persistStatus(self):
        if hasattr(self.output, 'writeJsonFile'):
            self.output.writeJsonFile()
        if hasattr(self.output, 'clearStatusValues'):
            self.output.clearStatusValues()

    def digestApiMsg(self, msg):
        m = ""
        try:
            m = (msg['message'])
        except KeyError:
            pass
        try:
            m = (msg['error'])
        except KeyError:
            pass
        return m

    @staticmethod
    def notify(msg, notify_conf):
        if notify_conf['enable_notifications']:
            send_notification(msg, notify_conf)
