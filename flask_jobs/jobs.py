import datetime

from dictabase import (
    BaseTable, FindAll, Delete,
)
import pickle
import threading


class Job(BaseTable):
    '''
    Acts like a python dict()

    key/values include:
    'id': int, # auto generated
    'dt': datetime.datetime # when the job should be executed
    'func': callable # the function to be called
    'args': tuple() # args to be passed to func
    'kwargs': dict() # kwargs to be passed to func
    '''

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self['status'] = 'pending'
        self._lockDoJob = threading.Lock()

    def DoJob(self):
        with self._lockDoJob:
            if self['status'] != 'pending':
                raise RuntimeError('Cannot DoJob() twice.')

            func = pickle.loads(self['func'])
            args = pickle.loads(self['args'])
            kwargs = pickle.loads(self['kwargs'])

            try:
                self['status'] = 'starting'
                ret = func(*args, **kwargs)
                self['status'] = 'complete'
            except Exception as e:
                ret = e
                self['status'] = 'error'
                self['error'] = str(e)

            return ret

    def Cancel(self):
        Delete(self)


class RepeatingJob(Job):
    def Refresh(self):
        nowDT = datetime.datetime.utcnow()
        if self['dt'] < nowDT:
            repeatCallback = pickle.loads(self['repeatCallback'])
            self['dt'] = repeatCallback()
            self['status'] = 'pending'

    def DoJob(self):
        super().DoJob()
        self.Refresh()


# At startup, check the JobStore database for any repeating jobs
for job in FindAll(RepeatingJob):
    job.Refresh()
