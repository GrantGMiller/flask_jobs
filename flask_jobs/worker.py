import datetime
import threading
from dictabase import FindAll, FindOne
from .jobs import Job


class Worker:
    def __init__(self):
        self._timer = None
        self._lock = threading.Lock()

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

            nextJobList = list(FindAll(Job, status='pending', _orderBy='dt', _limit=1))
            if len(nextJobList) > 0:
                nextJob = nextJobList[0]

                nextJobDT = nextJob['dt']  # UTC
                nowDT = datetime.datetime.utcnow()
                delta = (nextJobDT - nowDT).total_seconds()
                if delta < 0:
                    delta = 0
                self._timer = threading.Timer(delta, self._DoOneJob, args=[nextJob['id']])
                self._timer.start()

            else:
                self._timer = None

    def _DoOneJob(self, jobID):
        ret = None

        with self._lock:
            job = FindOne(Job, id=jobID)
            if job['status'] == 'pending':
                ret = job.DoJob()

        self.Refresh()
        return ret
