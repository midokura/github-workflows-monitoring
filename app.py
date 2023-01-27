from flask import Flask, request, abort

import logging
from const import GithubHeaders
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

app = Flask(__name__)

jobs = dict()

def parse_datetime(date: str) -> datetime:
    exp = "%Y-%m-%dT%H:%M:%SZ"
    return datetime.strptime(date, exp)

def validate_origin_github() -> bool:
    userAgent = request.headers.get("User-Agent")
    if not userAgent.startswith("GitHub-Hookshot"):
        _LOGGER.warning("User-Agent is {userAgent}")
        return False

    if request.headers.get("Content-Type") != "application/json":
        _LOGGER.warning("Content is not JSON")
        return False

    if not request.headers.get(GithubHeaders.EVENT.value):
        _LOGGER.warning("No GitHub Event received!")
        return False

    return True

def process_workflow_job():
    job = request.get_json()

    job_id = job["workflow_job"]["run_id"]
    name = job["workflow_job"]["workflow_name"]
    time_start = parse_datetime(job["workflow_job"]["started_at"])
    repository = job["repository"]["full_name"]
    action = job["action"]
    NOW = datetime.now()

    if action == "queued":
        # add to memory as timestamp
        jobs[job_id] = int(time_start.timestamp())
        msg = f"{NOW} {action=} {repository=} workflow={name} {job_id=} {time_start=}"

    elif action == "in_progress":
        job_requested = jobs.get(job_id, None)
        if not job_requested:
            _LOGGER.warning(f"Job {job_id} is {action} but not stored!")
            time_to_start = 0
        else:
            time_to_start = (
                time_start - datetime.fromtimestamp(job_requested)
            ).seconds
        msg = f"{NOW} {action=} {repository=} workflow={name} {job_id=} {time_to_start=}"

    elif action == "completed":
        job_requested = jobs.get(job_id, None)
        if not job_requested:
            _LOGGER.warning(f"Job {job_id} is {action} but not stored!")
            time_to_finish = 0
        else:
            time_to_finish = (
                time_start - datetime.fromtimestamp(job_requested)
            ).seconds
            # delete from memory
            del jobs[job_id]
        
        msg = f"{NOW} {action=} {repository=} workflow={name} {job_id=} {time_to_finish=}"

    print(msg)

    return True

@app.route("/github-webhook", methods=["POST"])
def github_webhook_process():
    if not validate_origin_github():
        return abort(401)

    event = request.headers.get(GithubHeaders.EVENT.value)
    command = f"process_{event}"

    #if hasattr(command) and callable(getattr(command)):
    if command == "process_workflow_job":
        _LOGGER.debug(f"Calling function {command}")
        #response = getattr(command)()
        response = process_workflow_job()

        if not response:
            _LOGGER.error(f"Error calling {event} function")
            return abort(500)
        return "OK"

    _LOGGER.error(f"Unknown event type {event}, can't handle")
    return abort(405)
