import sys
import time
import datetime
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
    def __init__(self):
        self.console = ConsoleOutput()
        self._lended = ''
	self.refreshStatus()

    def timestamp(self):
        ts = time.time()
        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    def log(self, msg):
        self.console.printline(self.timestamp() + ' ' + msg)
        self.refreshStatus()

    def offer(self, amt, cur, rate, days, msg):
	line = self.timestamp() + ' Placing ' + str(amt) + ' ' + str(cur) + ' at ' + str(float(rate)*100) + '% for ' + days + ' days... ' + self.digestApiMsg(msg)
	self.console.printline(line)
	self.refreshStatus()

    def cancelOrders(self, cur, msg):
	line = self.timestamp() + ' Canceling all ' + str(cur) + ' orders... ' + self.digestApiMsg(msg)
	self.console.printline(line)
	self.refreshStatus()

    def refreshStatus(self, lended=''):
	now = time.time()
	if lended != '':
		if len(lended) > 99:
			#truncate status, try preventing console bloating
			self._lended = str(lended)[:96] + '...' 
		else:
			self._lended = str(lended)
	self.console.status(self._lended)

    def digestApiMsg(self, msg):
	try:
	    m = (msg['message'])
	except KeyError:
	    pass
	try:
	    m = (msg['error'])
	except KeyError:
	    pass
	return m
