import datetime

from dictabase import (
    BaseTable, FindAll, Delete, Drop,
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

    def DoJob(self):
        # print('DoJob(self=', self)

        if self['status'] != 'pending':
            raise RuntimeError('This job has already been done.')

        try:
            func = pickle.loads(self['func'])
            args = pickle.loads(self['args'])
            kwargs = pickle.loads(self['kwargs'])
            self['status'] = 'starting'
            ret = func(*args, **kwargs)
            self['status'] = 'complete'
            self['error'] = ''
        except Exception as e:
            print('DoJob Exception:', e)
            ret = e
            self['status'] = 'error'
            self['error'] = str(e)

        if self['kind'] == 'repeat':
            self.Refresh()

        self['lastDoJobTime'] = datetime.datetime.utcnow()
        return ret

    def Delete(self):
        Delete(self)

    def Refresh(self):
        # print('Job.Refresh(self=', self)
        delta = datetime.timedelta(**self['deltaKwargs'])
        nextDT = self['dt']
        nowDT = datetime.datetime.utcnow()
        while nextDT < nowDT:
            nextDT += delta
        self['dt'] = nextDT
        self['status'] = 'pending'
        # print('after Job.Refresh(self=', self)
