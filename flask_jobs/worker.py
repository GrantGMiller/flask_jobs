import datetime
import threading
from dictabase import FindAll, FindOne
from .jobs import Job


class WorkerOld:
    def __init__(self):
        self._timer = None
        self._lock = threading.Lock()

        self._repeatJobsRefreshed = False
        self.queuedJob = None

    def _StopTimer(self):
        if self._timer:
            if self._timer.is_alive():
                self._timer.cancel()
            self.queuedJob = None

    def Refresh(self):
        '''
        Updates the self._timer
        :return:
        '''
        with self._lock:
            self._StopTimer()

            # At startup, the repeating jobs must be refreshed once
            if self._repeatJobsRefreshed is False:
                try:
                    for thisJob in FindAll(Job, kind='repeat'):
                        thisJob.Refresh()
                    self._repeatJobsRefreshed = True
                except Exception as e:
                    print('Error refreshing RepeatJobs', e)

            # do all the ASAP jobs now
            nextJob = None
            for job in FindAll(Job, status='pending', _orderBy='dt'):
                if job['kind'] == 'asap':
                    job.DoJob()
                else:
                    if nextJob is None:
                        nextJob = job

            if nextJob:
                nowDT = datetime.datetime.utcnow()
                nextJobDT = nextJob['dt']  # UTC
                delta = (nextJobDT - nowDT).total_seconds()
                if delta < 0:
                    # this job was supposed to happen in the past, do it now!
                    delta = 0
                print(f'46 nowDT={nowDT}, nextJobDT={nextJobDT}, delta={delta}, nextJob={nextJob}')
                self.queuedJob = nextJob
                self._timer = threading.Timer(delta, self._DoOneJob)
                self._timer.start()

    def _DoOneJob(self):
        ret = None
        with self._lock:
            self._StopTimer()
            if self.queuedJob:
                self.queuedJob.DoJob()
                self.queuedJob = None

        self.Refresh()
        return ret

    def __del__(self):
        self._StopTimer()


class Worker:
    def __init__(self):
        self._timer = None
        self._lock = threading.Lock()

    def Refresh(self, newTimeout=None):
        self.StopTimer()
        if newTimeout:
            self._timer = threading.Timer(newTimeout, self.DoJobs)
            self._timer.start()
        else:
            self.DoJobs()

    def StopTimer(self):
        if self._timer:
            if self._timer.is_alive():
                self._timer.cancel()

    def DoJobs(self):
        with self._lock:
            self.StopTimer()
            nowDT = datetime.datetime.utcnow()

            # Do all jobs that are past their self['dt']
            for job in FindAll(Job, status='pending', _orderBy='dt'):
                if job['dt'] < nowDT:
                    job.DoJob()

            # Find the next 'schedule' or 'repeat' Job
            nextJobList = list(FindAll(Job, status='pending', kind='schedule', _orderBy='dt', _limit=1))
            if not nextJobList:
                nextJobList = list(FindAll(Job, status='pending', kind='repeat', _orderBy='dt', _limit=1))
            # print('nextJobList=', nextJobList)
            if nextJobList:
                nextJob = nextJobList[0]
                delta = (nextJob['dt'] - nowDT).total_seconds()
                # print('delta=', delta)
                self.Refresh(delta)

    def __del__(self):
        self.StopTimer()