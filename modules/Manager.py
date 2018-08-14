from modules.BotWorker import BotWorker
import threading


class Manager:

    def __init__(self):
        global workerlist, workerthreads
        workerlist = {}
        workerthreads = {}
        pass

    def addlist(self,configlist):
        for config in configlist:
            self.add(config)

    def add(self, configname):
        workerlist[configname] = BotWorker(configname)

    def runall(self):
        for worker in workerlist:
            if workerlist[worker].isenabled():
                self.run(worker)

    def run(self, worker):
        work = workerlist[worker]
        # threading or async start a workers run command
        thread = threading.Thread(target=work.run)
        thread.deamon = True
        thread.start()

