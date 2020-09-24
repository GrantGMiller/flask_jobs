from crontab import CronTab
import sys
JOB_COMMENT = 'flask_jobs'

JOB_INTERVAL = 1  # minutes


def Setup(SERVER_HOST_URL):
    if not sys.platform.startswith('win'):
        cron = CronTab(user=True)
        for job in cron:
            if job.comment == JOB_COMMENT:
                job.clear()
                job.minutes.every(JOB_INTERVAL)
        else:
            # JOB_COMMENT not found
            job = cron.new(command=f'curl {SERVER_HOST_URL}/jobs/refresh', comment=JOB_COMMENT)
            job.minutes.every(1)
            cron.write()
