'''
All datetimes are in UTC
'''
import datetime
import pickle

from dictabase import (
    RegisterDBURI,
    New
)
from .jobs import Job, RepeatingJob
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
        kind='schedule'
    )
    # print('newJob=', newJob)
    _worker.Refresh()
    return newJob


def RepeatJob(repeatCallback, func, args=(), kwargs={}):
    '''
    :param repeatCallback: a function that should return the next call time as a datetime object
    :param func: callable
    :param args: tuple
    :param kwargs: dict
    :return:
    '''
    newJob = New(
        RepeatingJob,
        dt=repeatCallback(),
        repeatCallback=pickle.dumps(repeatCallback),
        func=pickle.dumps(func),
        args=pickle.dumps(args),
        kwargs=pickle.dumps(kwargs),
        kind='repeat'
    )
    # print('newJob=', newJob)
    _worker.Refresh()
    return newJob

_worker.Refresh()