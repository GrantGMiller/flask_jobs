import datetime
import threading
from .jobs import Job


class Worker:
    def __init__(self, db=None):
        self.running = True
        self._db = db
        self.logger = None
        self._timer = None
        self._lock = threading.Lock()
        self.Refresh()

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
                self.StopTimer()
                nowDT = datetime.datetime.utcnow()

                # Do all jobs that are past their self['dt']
                jobs = list(self._db.FindAll(Job, status='pending', _orderBy='dt'))

                for job in jobs:
                    if job['dt'] < nowDT:
                        job.DoJob(self)
                        del job  # forces the job to be committed to db

                # Find the next 'schedule' or 'repeat' Job
                nextJobList = list(self._db.FindAll(Job, status='pending', _orderBy='dt', _limit=1))

                if nextJobList:
                    nextJob = nextJobList[0]
                    delta = (nextJob['dt'] - nowDT).total_seconds()

                    self.Refresh(delta)
        else:
            self.print(f'DoJobs() called, but self.running is {self.running}')

    def print(self, *args):
        if self.logger:
            self.logger(f'{datetime.datetime.utcnow()}: ' + ' '.join([str(a) for a in args]))

    def __del__(self):
        self.Kill()

    def Kill(self):
        self.running = False
        self.StopTimer()
