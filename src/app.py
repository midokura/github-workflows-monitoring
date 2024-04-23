from datetime import datetime
import logging
from logging.config import dictConfig
import os

from flask import Flask, abort, request
from flask_apscheduler import APScheduler


from const import GithubHeaders, LOGGING_CONFIG
from github import GithubJob
from utils import parse_datetime, dict_to_logfmt

dictConfig(LOGGING_CONFIG)

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)

# set to WARNING to disable access log
log = logging.getLogger("werkzeug")
loglevel_flask = os.getenv("LOGLEVEL", "INFO")
if hasattr(logging, loglevel_flask):
    loglevel_flask = getattr(logging, loglevel_flask)
    log.setLevel(loglevel_flask)

jobs = dict()


# check all calls are valid
@app.before_request
def validate_origin_github():
    invalid = False
    userAgent = request.headers.get("User-Agent")
    if not userAgent.startswith("GitHub-Hookshot"):
        app.logger.warning(f"User-Agent is {userAgent}")
        invalid = True

    if request.headers.get("Content-Type") != "application/json":
        app.logger.warning("Content is not JSON")
        invalid = True

    if not request.headers.get(GithubHeaders.EVENT.value):
        app.logger.warning("No GitHub Event received!")
        invalid = True

    if invalid:
        return abort(401)


def process_workflow_job():
    job = GithubJob(request.get_json())

    context_details = {
        "action": job.action,
        "repository": job.repository,
        "branch": job.branch,
        "job_id": job.id,
        "run_id": job.run_id,
        "job_name": job.name,
        "workflow": job.workflow,
        "requestor": job.requestor,
    }

    if job.action == "queued":
        # add to memory
        jobs[job.id] = job

    elif job.action == "in_progress":
        job_requested = jobs.get(job.id)
        time_to_start = None
        if not job_requested:
            app.logger.warning(f"Job {job.id} is {job.action} but not stored!")
        else:
            if job.time_start < job_requested.time_start:
                app.logger.error(f"Job {job.id} was in progress before being queued")
                del jobs[job.id]
            else:
                time_to_start = (
                    job.time_start - job_requested.time_start
                ).seconds

        context_details = {
            **context_details,
            "runner_name": job.runner_name,
            "runner_public": job.runner_public,
            "repository_private": job.repository_private,
        }

        if time_to_start:
            context_details["time_to_start"] = time_to_start

    elif job.action == "completed":
        job_requested = jobs.get(job.id)
        if not job_requested:
            app.logger.warning(f"Job {job.id} is {job.action} but not stored!")
            time_to_finish = 0
        else:
            time_to_finish = (
                job.time_completed - job.time_start
            ).seconds
            # delete from memory
            del jobs[job.id]

        context_details = {
            **context_details,
            "runner_name": job.runner_name,
            "time_to_finish": time_to_finish,
            "conclusion": job.conclusion,
        }

    else:
        app.logger.warning(f"Unknown action {job.action}, removing from memory")
        if job.id in jobs:
            del jobs[job.id]
        context_details = None

    if context_details:
        app.logger.info(dict_to_logfmt(context_details))
    return True


@scheduler.task('interval', id='monitor_queued', seconds=30)
def monitor_queued_jobs():
    """ Return the job that has been queued and not starting for long time. """
    app.logger.debug("Starting monitor_queued_jobs")
    if not jobs:
        return

    job_id, time_start = min(jobs.items(), key=lambda x: x[1])
    delay = int(datetime.now().timestamp() - time_start)

    if delay <= int(os.getenv("QUEUED_JOBS_DELAY_THRESHOLD", 150)):
        return

    context_details = {
        "action": "monitor_queued",
        "job_id": job_id,
        "started_at": time_start,
        "delay": delay,
    }

    app.logger.info(dict_to_logfmt(context_details))


allowed_events = {"workflow_job": process_workflow_job}
scheduler.start()


@app.route("/github-webhook", methods=["POST"])
def github_webhook_process():
    event = request.headers.get(GithubHeaders.EVENT.value)

    if event in allowed_events:
        app.logger.debug(f"Calling function to process {event=}")
        func = allowed_events.get(event)
        func()
        return "OK"

    app.logger.error(f"Unknown event type {event}, can't handle")
    return abort(405)
