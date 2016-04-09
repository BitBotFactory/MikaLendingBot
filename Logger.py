import sys
import time
import datetime
import atexit
import json
import io
from RingBuffer import RingBuffer

class ConsoleOutput(object):
	def __init__(self):
		self._status = ''
		atexit.register(self._exit)

	def _exit(self):
		self._status += '  ' # In case the shell added a ^C
		self.status('')

	def status(self, msg, time=''):
		status = str(msg)
		if msg != '' and len(status) > 99:
			#truncate status, try preventing console bloating
			status = str(msg)[:96] + '...' 
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
		self.jsonOutputLog = RingBuffer(logLimit);

	def status(self, status, time):
		self.jsonOutput["last_update"] = time
		self.jsonOutput["last_status"] = status
		self.writeJsonFile()

	def printline(self, line):
		self.jsonOutputLog.append(line)
		
	def writeJsonFile(self):
		with io.open(self.jsonOutputFile, 'w', encoding='utf-8') as f:
			self.jsonOutput["log"] = self.jsonOutputLog.get()
			f.write(unicode(json.dumps(self.jsonOutput, ensure_ascii=False, sort_keys=True)))
			f.close()

class Logger(object):
	def __init__(self, jsonFile = '', jsonLogSize = -1):
		self._lended = ''
		if jsonFile != '' and jsonLogSize != -1:
			self.console = JsonOutput(jsonFile, jsonLogSize)
		else:
			self.console = ConsoleOutput()
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
		if lended != '':
			self._lended = lended;		
		self.console.status(self._lended, self.timestamp())
		
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
