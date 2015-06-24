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
