from datetime import datetime
from logging.config import dictConfig

from flask import Flask, abort, request

from const import GithubHeaders

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s]: %(levelname)s | %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

app = Flask(__name__)

jobs = dict()


def parse_datetime(date: str) -> datetime:
    exp = "%Y-%m-%dT%H:%M:%SZ"
    return datetime.strptime(date, exp)


def validate_origin_github() -> bool:
    userAgent = request.headers.get("User-Agent")
    if not userAgent.startswith("GitHub-Hookshot"):
        app.logger.warning("User-Agent is {userAgent}")
        return False

    if request.headers.get("Content-Type") != "application/json":
        app.logger.warning("Content is not JSON")
        return False

    if not request.headers.get(GithubHeaders.EVENT.value):
        app.logger.warning("No GitHub Event received!")
        return False

    return True


def get_message(*args):
    msg = list()
    for variable in args:
        var_name = f"{variable=}".split("=")[0]
        msg.append(f'{var_name}="{variable}"')
    return " ".join(msg)


def process_workflow_job():
    job = request.get_json()

    job_id = job["workflow_job"]["run_id"]
    workflow = job["workflow_job"]["workflow_name"]
    time_start = parse_datetime(job["workflow_job"]["started_at"])
    repository = job["repository"]["full_name"]
    action = job["action"]

    if action == "queued":
        # add to memory as timestamp
        jobs[job_id] = int(time_start.timestamp())
        msg = get_message(action, repository, job_id, workflow)

    elif action == "in_progress":
        job_requested = jobs.get(job_id)
        if not job_requested:
            app.logger.warning(f"Job {job_id} is {action} but not stored!")
            time_to_start = 0
        else:
            time_to_start = (time_start - datetime.fromtimestamp(job_requested)).seconds
        msg = get_message(action, repository, job_id, time_to_start, workflow)

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
        msg = get_message(action, repository, job_id, time_to_finish, workflow)
    else:
        app.logger.warning(f"Unknown action {action}, removing from memory")
        if job_id in jobs:
            del jobs[job_id]

    app.logger.info(msg)
    return True


@app.route("/github-webhook", methods=["POST"])
def github_webhook_process():
    if not validate_origin_github():
        return abort(401)

    event = request.headers.get(GithubHeaders.EVENT.value)
    command = f"process_{event}"

    if command == "process_workflow_job":
        app.logger.debug(f"Calling function {command}")
        response = process_workflow_job()

        if not response:
            app.logger.error(f"Error calling {event} function")
            return abort(500)
        return "OK"

    app.logger.error(f"Unknown event type {event}, can't handle")
    return abort(405)
