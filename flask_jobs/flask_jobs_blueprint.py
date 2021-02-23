from flask import (
    Blueprint,
)

from flask_jobs import Job

bp = Blueprint('jobs', __name__)

app = None


@bp.record
def Record(state):
    global app
    app = state.app


@bp.route('/jobs/refresh')
def JobsRefresh():
    print('JobsRefresh()')
    app.jobs.print('JobsRefresh()')
    app.jobs.RefreshWorker()
    return 'Job Worker Refreshed'


@bp.route('/jobs/delete_old')
def JobsDeleteOld():
    print('JobsDeleteOld()')
    count = 0
    for job in app.jobs.db.FindAll(Job, kind='asap', status='complete'):
        app.jobs.db.Delete(job)
        count += 1
    return 'Deleted {} old jobs'.format(count)

