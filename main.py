import datetime
import time

from flask import Flask, render_template, redirect, jsonify
from flask_jobs import JobScheduler

app = Flask('JobApp')
jobs = JobScheduler(
    app,
    # logger=lambda *a, **k: print(*a, **k),
    SERVER_HOST_URL='http://127.0.0.1:5000/',
    deleteOldJobs=False,
)


def Callback(*a, **k):
    print('Callback(', a, k)
    return 'This string was returned by the Callback() function'


@app.route('/')
def Index():
    return render_template(
        'index.html',
        jobs=jobs.GetJobs(),
        utcnow=datetime.datetime.utcnow(),
    )


@app.route('/add_now_job')
def NowJob():
    jobs.AddJob(
        func=Callback,
        args=('Now Job now={}'.format(datetime.datetime.utcnow()),),
        kwargs={'one': 'won', 'two': 'too'},
        name='Now Job at {}'.format(time.asctime()),
        successCallback=SuccessCallback,
        errorCallback=ErrorCallback,
    )
    return redirect('/')


@app.route('/add_later_job')
def LaterJob():
    dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=5)
    jobs.ScheduleJob(
        dt=dt,
        func=Callback,
        args=('ScheduleJob now={}, dt={}'.format(
            datetime.datetime.utcnow(),
            dt
        ),),
        kwargs={'one': 'won', 'two': 'too'},
        name='ScheduleJob Job at {}'.format(time.asctime()),
        successCallback=SuccessCallback,
        errorCallback=ErrorCallback,
    )
    return redirect('/')


@app.route('/add_repeat_job')
def Repeat():
    dt = datetime.datetime.utcnow()
    jobs.RepeatJob(
        startDT=dt,
        func=Callback,
        args=('RepeatJob now={}, dt={}'.format(
            datetime.datetime.utcnow(),
            dt
        ),),
        kwargs={'one': 'won', 'two': 'too'},
        name='RepeatJob Job at {}'.format(time.asctime()),
        seconds=10,
        successCallback=SuccessCallback,
        errorCallback=ErrorCallback,
    )
    return redirect('/')


@app.route('/add_fail_job')
def Fail():
    jobs.AddJob(
        func=Nope,
        args=('Now Job now={}'.format(datetime.datetime.utcnow()),),
        kwargs={'one': 'won', 'two': 'too'},
        name='Now Job at {}'.format(time.asctime()),
        successCallback=SuccessCallback,
        errorCallback=ErrorCallback,
    )
    return redirect('/')


def Nope(*a, **k):
    raise Exception('Nope() function raising exception')


def SuccessCallback(j):
    print('SuccessCallback(j=', j)


def ErrorCallback(j):
    print('ErrorCallback(j=', j)


@app.route('/delete/<ID>')
def Delete(ID):
    job = jobs.GetJob(int(ID))
    job.Delete()
    return redirect('/')


@app.route('/jobs_json')
def JobsJson():
    return jsonify([job.dict() for job in jobs.GetJobs()])


if __name__ == '__main__':
    app.run(
        debug=True,
        threaded=True,
    )
