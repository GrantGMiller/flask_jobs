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
        self._lockDoJob = threading.Lock()

    def DoJob(self):
        with self._lockDoJob:
            # print('29 DoJob()', self['id'], self)
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
                print('DoJob Exception:', e)
                ret = e
                self['status'] = 'error'
                self['error'] = str(e)

            if self['kind'] == 'repeat':
                self.Refresh()

            return ret

    def Cancel(self):
        Delete(self)

    def Refresh(self):
        if self['status'] != 'pending':
            oldDT = self['dt']
            self['dt'] = self._GetNextRepeatDT()
            newDT = self['dt']
            # if newDT - oldDT > datetime.timedelta(**self['deltaKwargs']):

            # print('self=', self)
            # print('oldDT=', oldDT)
            # print('newDT=', newDT)
            # print('nowDT=', datetime.datetime.utcnow())
            # print('newDT-oldDT=', newDT - oldDT)
            # print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^', self['deltaKwargs'])
            self['status'] = 'pending'

    def _GetNextRepeatDT(self):
        nowDT = datetime.datetime.utcnow()
        if self['dt'] > nowDT:
            return self['dt']

        delta = datetime.timedelta(**self['deltaKwargs'])
        if delta.total_seconds() <= 0:
            raise ValueError('delta must be greater than 0')

        nextDT = self['dt']
        while nextDT < nowDT:
            # keep adding the delta until its in the future
            nextDT = nextDT + delta

        return nextDT
