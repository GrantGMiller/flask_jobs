An easy job scheduling interface for flask projects.

Install
=======
pip install flask_jobs


Example Flask Project
--------------------------

::

    import datetime
    import time

    from flask import Flask, render_template, redirect
    from flask_jobs import JobScheduler

    app = Flask('JobApp')
    jobs = JobScheduler(app)


    def Callback(*a, **k):
        print('Callback(', a, k)


    @app.route('/')
    def Index():
        return render_template(
            'index.html',
            jobs=jobs.GetJobs(),
            utcnow=datetime.datetime.utcnow(),
        )


    @app.route('/add_now_job')
    def NowJob():
        # Schedule a job to happen ASAP
        jobs.AddJob(
            func=Callback,
            args=('Now Job now={}'.format(datetime.datetime.utcnow()),),
            kwargs={'one': 'won', 'two': 'too'},
            name='Now Job at {}'.format(time.asctime())
        )
        return redirect('/')


    @app.route('/add_later_job')
    def LaterJob():
        # Schedule a job to happen once in the future
        dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=5)
        jobs.ScheduleJob(
            dt=dt,
            func=Callback,
            args=('ScheduleJob now={}, dt={}'.format(
                datetime.datetime.utcnow(),
                dt
            ),),
            kwargs={'one': 'won', 'two': 'too'},
            name='ScheduleJob Job at {}'.format(time.asctime())
        )
        return redirect('/')


    @app.route('/add_repeat_job')
    def Repeat():
        # Schedule a job to repeat at the given interval
        dt = datetime.datetime.utcnow()
        jobs.RepeatJob(
            startDT=dt, # The first time to run (None if you want to start right now)
            func=Callback,
            args=('RepeatJob now={}, dt={}'.format(
                datetime.datetime.utcnow(),
                dt
            ),),
            kwargs={'one': 'won', 'two': 'too'},
            name='RepeatJob Job at {}'.format(time.asctime()),
            seconds=10, # can also pass "weeks", "days", "minutes", "hours"
        )
        return redirect('/')


    @app.route('/delete/<ID>')
    def Delete(ID):
        job = jobs.GetJob(int(ID))
        job.Delete()
        return redirect('/')


    if __name__ == '__main__':
        app.run(
            debug=True,
            threaded=True,
        )
