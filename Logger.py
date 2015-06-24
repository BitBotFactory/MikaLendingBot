import sys
import time
import atexit

class ConsoleOutput(object):
    def __init__(self):
        self._status = ''
        atexit.register(self._exit)

    def _exit(self):
        self._status += '  ' # In case the shell added a ^C
        self.status('')

    def status(self, status):
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

class Logger(object):
    def __init__(self, core):
        self.console = ConsoleOutput()

    def timestamp():
        ts = time.time()
        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    def logOffer(self, amt, cur, rate, days):
	line = timestamp() + ' Placing ' + str(amt) + ' ' + str(cur) + ' at ' + str(float(rate)*100) + '% for ' + days + ' days... '
	self.console.printline(line)

    def refreshStatus(self):
	now = time.time()
