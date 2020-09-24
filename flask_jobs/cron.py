from crontab import CronTab
import sys
import hashlib

JOB_INTERVAL = 1  # minutes


def Setup(SERVER_HOST_URL):
    if not sys.platform.startswith('win'):

        JOB_COMMENT = 'flask_jobs_' + HashIt(SERVER_HOST_URL)[:10]  # create a unique cron job per host
        command = f'curl {SERVER_HOST_URL}/jobs/refresh'


        cron = CronTab(user=True)
        # remove any bad jobs that were created by flask_jobs==1.0.0
        for job in cron:
            if job.comment == 'flask_jobs' and job.command == command:
                # these files were created by flask_jobs==1.0.0 and need to be removed
                cron.remove(job)

        # create the new job if it does not exist
        for job in cron:
            if job.comment == JOB_COMMENT:
                # job already exist, make sure it is set to the right interval
                job.clear()
                job.minutes.every(JOB_INTERVAL)
                break

        else:
            # JOB_COMMENT not found
            job = cron.new(command=command, comment=JOB_COMMENT)
            job.minutes.every(1)

        cron.write()


def HashIt(strng, salt=''):
    hash1 = hashlib.sha512(bytes(strng, 'utf-8')).hexdigest()
    hash1 += salt
    hash2 = hashlib.sha512(bytes(hash1, 'utf-8')).hexdigest()
    return hash2
