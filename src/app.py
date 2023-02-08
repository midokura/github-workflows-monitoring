from datetime import datetime
import logging
from logging.config import dictConfig
import os

from flask import Flask, abort, request


from const import GithubHeaders, LOGGING_CONFIG
from utils import parse_datetime

dictConfig(LOGGING_CONFIG)

app = Flask(__name__)

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
    job = request.get_json()

    job_id = job["workflow_job"]["id"]
    workflow = job["workflow_job"]["workflow_name"]
    time_start = parse_datetime(job["workflow_job"]["started_at"])
    repository = job["repository"]["full_name"]
    action = job["action"]

    if action == "queued":
        # add to memory as timestamp
        jobs[job_id] = int(time_start.timestamp())
        msg = (
            f"action={action} repository={repository} job_id={job_id}"
            f' workflow="{workflow}"'
        )

    elif action == "in_progress":
        job_requested = jobs.get(job_id)
        if not job_requested:
            app.logger.warning(f"Job {job_id} is {action} but not stored!")
            time_to_start = 0
        else:
            time_to_start = (time_start - datetime.fromtimestamp(job_requested)).seconds
        msg = (
            f"action={action} repository={repository} job_id={job_id}"
            f' workflow="{workflow}" time_to_start={time_to_start}'
        )

    elif action == "completed":
        job_requested = jobs.get(job_id)
        if not job_requested:
            app.logger.warning(f"Job {job_id} is {action} but not stored!")
            time_to_finish = 0
        else:
            time_to_finish = (
                parse_datetime(job["workflow_job"]["completed_at"]) - time_start
            ).seconds
            # delete from memory
            del jobs[job_id]
        msg = (
            f"action={action} repository={repository} job_id={job_id}"
            f' workflow="{workflow}" time_to_finish={time_to_finish}'
        )
    else:
        app.logger.warning(f"Unknown action {action}, removing from memory")
        if job_id in jobs:
            del jobs[job_id]
        msg = None

    if msg:
        app.logger.info(msg)
    return True


allowed_events = {
    "workflow_job": process_workflow_job
}


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
