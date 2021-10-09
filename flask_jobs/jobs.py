import datetime
import flask_dictabase
import pickle


class Job(flask_dictabase.BaseTable):
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
        self['status'] = k.get('status', 'pending')

    def DoJob(self, worker):
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

            try:
                self.Set('result', ret)
            except Exception as e:
                print('42 Exception', e)
                self.Set('result', str(ret))

            try:
                callbackSuccess = pickle.loads(self['successCallback'])
                if callbackSuccess:
                    callbackSuccess(self)
            except Exception as e:
                print('Error calling successCallback(job):' + str(e))

        except Exception as e:
            print('DoJob Exception:', e)
            ret = e
            self['status'] = 'error'
            self['error'] = str(e)

            try:
                callbackError = pickle.loads(self['errorCallback'])
                if callbackError:
                    callbackError(self)
            except Exception as e:
                print('Error calling errorCallback(job):' + str(e))

        if self['kind'] == 'repeat':
            self.Refresh()
            worker.Refresh()

        self['lastDoJobTime'] = datetime.datetime.utcnow()

        return ret

    def Delete(self):
        '''
        Use this to cancel a job that has not yet completed.
        :return:
        '''
        self.db.Delete(self)

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

    def dict(self):
        return {
            'status': self['status'],
            'lastDoJobTime': self['lastDoJobTime'],
            'dt': self['dt'],
            'kind': self['kind'],
            'error': self['error'],
            'result': self.Get('result', None),
            'name': self['name'],
        }
