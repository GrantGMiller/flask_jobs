'''
All datetimes are in UTC

When you use AddJob, the job is executed ASAP.
On Linux, ScheduleJob and RepeatJob may be up to 1 minute delayed, but they will execute.
On Windows, ScheduleJob and RepeatJob will be executed at the exact time (within a few milliseconds, depending on your system)

'''
import datetime
import pickle
from .jobs import Job
from .worker import Worker
import flask_dictabase
from .flask_jobs_blueprint import bp
from . import cron
import sys


class JobScheduler:
    def __init__(self, app=None, logger=None, SERVER_HOST_URL=None, deleteOldJobs=False):
        '''

        :param app:
        :param logger:
        :param SERVER_HOST_URL:
        :param deleteOldJobs: bool > True means delete jobs from database after they complete
        '''
        if SERVER_HOST_URL is None and not sys.platform.startswith('win'):
            raise KeyError('On linux, you must provide a SERVER_HOST_URL such as "http://mysite.com/')
        self.SERVER_HOST_URL = SERVER_HOST_URL
        self.app = app
        self.db = None
        self.worker = None
        self.logger = logger
        self.crontab = None
        self.deleteOldJobs = deleteOldJobs

        if app is not None:
            self.init_app(app)

    def print(self, *args):
        if self.logger:
            self.logger(f'{datetime.datetime.utcnow()}: ' + ' '.join([str(a) for a in args]))

    def init_app(self, app):
        self.print('JobScheduler.init_app(app=', app)

        if not hasattr(app, 'db'):
            self.db = flask_dictabase.Dictabase(app)
        else:
            self.db = app.db

        app.jobs = self

        app.register_blueprint(bp)
        cron.Setup(self.SERVER_HOST_URL)

        self.worker = Worker(app, self.db)
        self.worker.deleteOldJobs = self.deleteOldJobs
        self.worker.logger = self.logger

        app.teardown_appcontext(self.teardown)

    def teardown(self, exception):
        # This gets called after every request
        # DO NOT kill the worker thread
        self.print('JobScheduler.teardown_appcontext(exception=', exception)
        pass

    def AddJob(self, func, args=(), kwargs={}, name=None, success=None, error=None):
        '''
        Schedule a job to be run ASAP
        :param func: callable
        :param args: tuple
        :param kwargs: dict
        :param success: function takes one argument (the job object)
        :param error: function takes one argument (the job object)
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
            success=pickle.dumps(success),
            error=pickle.dumps(error),
        )
        if self.worker:
            self.worker.Refresh()
        return newJob

    def ScheduleJob(self, dt, func, args=(), kwargs={}, name=None, success=None, error=None):
        '''
        Schedule a job to be run once at a future time
        :param dt: datetime in UTC
        :param func: callable
        :param args: tuple
        :param kwargs: dict
        :param success: function takes one argument (the job object)
        :param error: function takes one argument (the job object)
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
            success=pickle.dumps(success),
            error=pickle.dumps(error),
        )
        if self.worker:
            self.worker.Refresh()
        return newJob

    def RepeatJob(self, startDT=None, func=None, args=(), kwargs={}, name=None, , success=None, error=None, **k):
        '''
        :param startDT: the first datetime that this job is executed. All future jobs will be calculated from this value.
        :param func: callable
        :param args: tuple
        :param kwargs: dict
        :param name: str - used to give the job a friendly name
        :param k: weeks, days, hours, minutes, seconds (anything supported by datetime.timedelta.__init__
        :param success: function takes one argument (the job object)
        :param error: function takes one argument (the job object)
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
            success=pickle.dumps(success),
            error=pickle.dumps(error),
        )

        if self.worker:
            self.worker.Refresh()
        return newJob

    def GetJobs(self, ):
        for job in self.db.FindAll(Job, status='pending', _orderBy='dt'):
            yield job

    def GetJob(self, jobID):
        return self.db.FindOne(Job, id=jobID)

    def RefreshWorker(self):
        self.worker.Refresh()

    def KillWorker(self):
        self.worker.Kill()

    def ReviveWorker(self):
        self.worker.running = True
        self.worker.Refresh()
