An easy job scheduling interface for flask projects.

Install
=======
pip install flask_jobs


Schedule a job to run ASAP
--------------------------

::

    from flask_jobs import AddJob

    def Callback(*args, **kwargs):
        print('The Callback function was called with args=', args, ' and kwargs=', kwargs)

    newJob = AddJob(
        func=Callback,
        a=(1, 'two', {'three': '4'}),
        k={'key': 'word'},
    )

    # The job will be run in a separate thread ASAP.

    # You can check the status of your job
    print('newJob['status']=', newJob['status']) # will return 'pending' or 'complete' or 'error'
    >> newJob['status']= complete

Schedule a job to happen once in the future
-------------------------------------------

::

    from flask_jobs import ScheduleJob
    import datetime

    def Callback(*args, **kwargs):
        print('The Callback function was called with args=', args, ' and kwargs=', kwargs)

    newJob = ScheduleJob(
        dt=datetime.datetime.utcnow() + datetime.timedelta(seconds=10), # all datetimes are in UTC
        func=Callback,
        a=(1, 'two', {'three': '4'}),
        k={'key': 'word'},
    )

    # The job will be run in a separate thread ASAP.

    # You can check the status of your job
    print('newJob['status']=', newJob['status']) # will return 'pending' or 'complete' or 'error'
    >> newJob['status']= pending
    # wait 10 seconds
    print('newJob['status']=', newJob['status'])
    >> newJob['status']= complete

Schedule a job to repeat indefinitely
-------------------------------------

::

    from flask_jobs import RepeatJob

    def Callback(*args, **kwargs):
        print('The Callback function was called with args=', args, ' and kwargs=', kwargs)

    RepeatJob(
        dt=datetime.datetime.utcnow(),
        seconds=30,
        func=JobCallback,
        args=('Repeating',),
        kwargs={'key': 'val'}
    )

    # All jobs are persistent. Even if you restart your server.