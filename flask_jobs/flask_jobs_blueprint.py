from flask import (
    Blueprint,
)

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
