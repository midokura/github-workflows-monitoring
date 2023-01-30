from datetime import datetime, timedelta
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


def prune_jobs():
    # if the first job is older than 2 days, prune all jobs older than 2 days
    # this might happen due to not completed jobs
    if datetime.fromtimestamp(list(jobs.values())[0]) > datetime.now() - timedelta(
        days=2
    ):
        app.logger.info("Pruning jobs")
        for job_id, timestamp in jobs.items():
            if (datetime.now() - datetime.fromtimestamp(timestamp)).days >= 2:
                del jobs[job_id]


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
        msg = f'{action=} {repository=} {job_id=} workflow="{workflow}"'
        prune_jobs()

    elif action == "in_progress":
        job_requested = jobs.get(job_id)
        if not job_requested:
            app.logger.warning(f"Job {job_id} is {action} but not stored!")
            time_to_start = 0
        else:
            time_to_start = (time_start - datetime.fromtimestamp(job_requested)).seconds
        msg = (
            f'{action=} {repository=} {job_id=} {time_to_start=} workflow="{workflow}"'
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
            f'{action=} {repository=} {job_id=} {time_to_finish=} workflow="{workflow}"'
        )

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
