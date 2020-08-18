'''
All datetimes are in UTC
'''
import datetime
import pickle
from .jobs import Job
from .worker import Worker
import dataset
from flask import _app_ctx_stack, current_app
import flask_dictabase


class JobScheduler:
    def __init__(self, app=None):
        self.app = app
        self.db = None
        self.worker = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.db = flask_dictabase.Dictabase(app)  # adds the app.db value
        self.worker = Worker(self.db)

    def AddJob(self, func, args=(), kwargs={}, name=None):
        '''
        Schedule a job to be run ASAP
        :param func: callable
        :param args: tuple
        :param kwargs: dict
        :return:
        '''
        newJob = self.db.New(
            Job,
            dt=datetime.datetime.utcnow(),
            func=pickle.dumps(func),
            args=pickle.dumps(args),
            kwargs=pickle.dumps(kwargs),
            kind='asap',
            name=name,
        )
        if self.worker:
            self.worker.Refresh()
        return newJob

    def ScheduleJob(self, dt, func, args=(), kwargs={}, name=None):
        '''
        Schedule a job to be run once at a future time
        :param dt: datetime in UTC
        :param func: callable
        :param args: tuple
        :param kwargs: dict
        :return:
        '''
        newJob = self.db.New(
            Job,
            dt=dt,
            func=pickle.dumps(func),
            args=pickle.dumps(args),
            kwargs=pickle.dumps(kwargs),
            kind='schedule',
            name=name,
        )
        if self.worker:
            self.worker.Refresh()
        return newJob

    def RepeatJob(self, startDT=None, func=None, args=(), kwargs={}, name=None, **k):
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

        newJob = self.db.New(
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

        if self.worker:
            self.worker.Refresh()
        return newJob

    def GetJobs(self, ):
        for job in self.db.FindAll(Job, status='pending', _orderBy='dt'):
            yield job

    def GetJob(self, jobID):
        return self.db.FindOne(Job, id=jobID)
