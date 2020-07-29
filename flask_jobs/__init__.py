'''
All datetimes are in UTC
'''
import datetime
import pickle

from dictabase import (
    RegisterDBURI,
    New, FindAll, FindOne
)
from .jobs import Job
from .worker import Worker

RegisterDBURI('sqlite:///JobStore.db')

_worker = Worker()


def AddJob(func, args=(), kwargs={}):
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
    )
    _worker.Refresh()
    return newJob


def ScheduleJob(dt, func, args=(), kwargs={}):
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
    )
    # print('newJob=', newJob)
    _worker.Refresh()
    return newJob


def RepeatJob(startDT=None, func=None, args=(), kwargs={}, **k):
    '''
    :param func: callable
    :param args: tuple
    :param kwargs: dict
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
    )
    # print('newJob=', newJob)
    _worker.Refresh()
    return newJob


def GetJobs():
    for job in FindAll(Job, status='pending'):
        yield job


def GetJob(jobID):
    return FindOne(Job, id=jobID)


_worker.Refresh()
