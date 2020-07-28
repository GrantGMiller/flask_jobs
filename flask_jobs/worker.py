import datetime
import threading
from dictabase import FindAll, FindOne
from .jobs import Job


class Worker:
    def __init__(self):
        self._timer = None
        self._lock = threading.Lock()

        self._repeatJobsRefreshed = False

    def Refresh(self):
        '''
        Updates the self._timer
        :return:
        '''
        with self._lock:
            if self._timer:
                if self._timer.is_alive():
                    self._timer.cancel()
                else:
                    self._timer = None

            # At startup, the repeating jobs must be refreshed once
            if self._repeatJobsRefreshed is False:
                try:
                    for job in FindAll(Job, kind='repeat'):
                        job.Refresh()
                    self._repeatJobsRefreshed = True
                except Exception as e:
                    print('Error refreshing RepeatJobs', e)

            nextJob = None
            for job in FindAll(Job, status='pending'):
                if nextJob is None or nextJob['dt'] > job['dt']:
                    nextJob = job

            if nextJob:
                nextJobDT = nextJob['dt']  # UTC
                nowDT = datetime.datetime.utcnow()
                delta = (nextJobDT - nowDT).total_seconds()
                if delta < 0:
                    delta = 0
                self._timer = threading.Timer(delta, self._DoOneJob, args=[type(nextJob), nextJob['id']])
                self._timer.start()

            else:
                self._timer = None

    def _DoOneJob(self, typ, jobID):
        ret = None

        with self._lock:
            job = FindOne(typ, id=jobID)
            if job['status'] == 'pending':
                # print('57 DoJob()', job['id'], job)
                ret = job.DoJob()

        self.Refresh()
        return ret

    def __del__(self):
        if self._timer and self._timer.is_alive():
            self._timer.cancel()
            self._timer = None
