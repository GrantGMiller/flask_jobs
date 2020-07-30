'''
All datetimes are in UTC
'''
import datetime
import pickle
from dictabase import RegisterDBURI as dictabase_RegisterDBURI
from dictabase import (
    New, FindAll, FindOne,

)
from .jobs import Job
from .worker import Worker


class WorkerManager:
    def __init__(self):
        self._workers = []

    @property
    def AllWorkers(self):
        return self._workers.copy()

    def RegisterNewWorker(self, thisWorker):
        if thisWorker not in self._workers:
            self._workers.append(thisWorker)
        self.RefreshAllWorkers()
        print('23 workers=', len(self._workers))

    def RemoveWorker(self, thisWorker):
        if thisWorker in self._workers:
            self._workers.remove(thisWorker)
        self.RefreshAllWorkers()
        print('23 workers=', len(self._workers))

    def RefreshAllWorkers(self, calledFromWorker=None):
        for thisWorker in self._workers:
            if thisWorker != calledFromWorker:
                thisWorker.Refresh()

    def KillAllWorkers(self):
        for thisWorker in self._workers.copy():
            thisWorker.Kill()
            self.RemoveWorker(thisWorker)


workerManager = WorkerManager()


def init_app(app=None):
    if app:
        dictabase_RegisterDBURI(app.config['DATABASE_URL'])
    else:
        dictabase_RegisterDBURI()

    if len(workerManager.AllWorkers) == 0: # limit to 1 worker for now
        thisWorker = Worker()
        workerManager.RegisterNewWorker(thisWorker)

    app.teardown_appcontext(workerManager.KillAllWorkers)


def AddJob(func, args=(), kwargs={}, name=None):
    '''
    Schedule a job to be run ASAP
    :param func: callable
    :param args: tuple
    :param kwargs: dict
    :return:
    '''
    newJob = New(
        Job,
        dt=datetime.datetime.utcnow(),
        func=pickle.dumps(func),
        args=pickle.dumps(args),
        kwargs=pickle.dumps(kwargs),
        kind='asap',
        name=name,
    )
    workerManager.RefreshAllWorkers()
    return newJob


def ScheduleJob(dt, func, args=(), kwargs={}, name=None):
    '''
    Schedule a job to be run once at a future time
    :param dt: datetime
    :param func: callable
    :param args: tuple
    :param kwargs: dict
    :return:
    '''
    newJob = New(
        Job,
        dt=dt,
        func=pickle.dumps(func),
        args=pickle.dumps(args),
        kwargs=pickle.dumps(kwargs),
        kind='schedule',
        name=name,
    )
    # print('newJob=', newJob)
    workerManager.RefreshAllWorkers()
    return newJob


def RepeatJob(startDT=None, func=None, args=(), kwargs={}, name=None, **k):
    '''
    :param startDT: the first datetime that this job is executed. All future jobs will be calculated from this value.
    :param func: callable
    :param args: tuple
    :param kwargs: dict
    :param name: str - used to give the job a friendly name
    :param k: weeks, days, hours, minutes, seconds (anything supported by datetime.timedelta.__init__
    :return:
    '''
    if len(k) == 0:
        raise KeyError('You must pass one of the following kwargs (weeks, days, hours, minutes, seconds)')
    startDT = startDT or datetime.datetime.utcnow()

    newJob = New(
        Job,
        startDT=startDT,
        dt=startDT,
        func=pickle.dumps(func),
        args=pickle.dumps(args),
        kwargs=pickle.dumps(kwargs),
        kind='repeat',
        deltaKwargs=k,
        name=name,
    )
    # print('newJob=', newJob)
    workerManager.RefreshAllWorkers()
    return newJob


def GetJobs():
    for job in FindAll(Job, status='pending'):
        yield job


def GetJob(jobID):
    return FindOne(Job, id=jobID)


workerManager.RefreshAllWorkers()
