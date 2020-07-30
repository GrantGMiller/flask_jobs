import datetime
import threading
from dictabase import FindAll, FindOne
from .jobs import Job


class Worker:
    def __init__(self, manager=None):
        self._running = True
        self._manager = manager
        self._timer = None
        self._lock = threading.Lock()

    def Refresh(self, newTimeout=0):
        if self._manager:
            self._manager.RefreshAllWorkers(calledFromWorker=self)
        self.StopTimer()
        self._timer = threading.Timer(newTimeout, self.DoJobs)
        self._timer.start()

    def StopTimer(self):
        if self._timer:
            if self._timer.is_alive():
                self._timer.cancel()

    def DoJobs(self):
        if self._running:
            with self._lock:
                self.StopTimer()
                nowDT = datetime.datetime.utcnow()

                # Do all jobs that are past their self['dt']
                for job in FindAll(Job, status='pending', _orderBy='dt'):
                    if job['dt'] < nowDT:
                        job.DoJob(self)
                        del job # forces the job to be committed to db

                # Find the next 'schedule' or 'repeat' Job
                nextJobList = list(FindAll(Job, status='pending', _orderBy='dt', _limit=1))
                # print('nextJobList=', nextJobList)
                if nextJobList:
                    nextJob = nextJobList[0]
                    delta = (nextJob['dt'] - nowDT).total_seconds()
                    # print('delta=', delta)
                    self.Refresh(delta)

    def __del__(self):
        self._running = False
        self.StopTimer()

    def Kill(self):
        self._running = False
        self.StopTimer()
