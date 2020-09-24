import datetime
import sys
import threading
from .jobs import Job

class Worker:
    def __init__(self, app=None, db=None):

        self.running = True
        self.app = app
        self._db = db
        self.logger = None
        self._timer = None
        self._lock = threading.Lock()
        self.Refresh()
        self.print('Worker.__init__(app=', app, ', db=', db)

    def Refresh(self, newTimeout=0.1):
        self.StopTimer()
        self._timer = threading.Timer(newTimeout, self.DoJobs)
        self._timer.start()

    def StopTimer(self):
        if self._timer:
            if self._timer.is_alive():
                self._timer.cancel()

    def DoJobs(self):
        if self.running:
            with self._lock:
                with self.app.app_context():
                    self.StopTimer()
                    nowDT = datetime.datetime.utcnow()

                    # Do all jobs that are past their self['dt']
                    jobs = list(self._db.FindAll(Job, status='pending', _orderBy='dt'))

                    for job in jobs:
                        if job['dt'] < nowDT:
                            job.DoJob(self)
                            del job  # forces the job to be committed to db

                    # on linux the refresh is triggered by a cron job
                    if sys.platform.startswith('win'):
                        # Find the next 'schedule' or 'repeat' Job
                        nextJobList = list(self._db.FindAll(Job, status='pending', _orderBy='dt', _limit=1))

                        if nextJobList:
                            nextJob = nextJobList[0]
                            delta = (nextJob['dt'] - nowDT).total_seconds()

                            if delta > 10:
                                delta = 10

                            self.Refresh(delta)
        else:
            self.print(f'DoJobs() called, but self.running is {self.running}')

    def print(self, *args):
        if self.logger:
            self.logger(f'{datetime.datetime.utcnow()}: ' + ' '.join([str(a) for a in args]))

    def __del__(self):
        self.Kill()

    def Kill(self):
        self.print('Worker.Kill()')
        self.running = False
        self.StopTimer()
