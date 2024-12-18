from datetime import datetime
import logging
from logging.config import dictConfig
import os

from flask import Flask, abort, request
from flask_apscheduler import APScheduler


from const import GithubHeaders, LOGGING_CONFIG
from github import GithubJob
from jobs import JobEventsHandler
from utils import dict_to_logfmt, parse_datetime
from query_graphql import query_jobs

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
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

jobs = dict()
job_handler = JobEventsHandler()


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
    event = request.get_json()
    job_handler.process_event(event)

    job = GithubJob(event)

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
                time_to_start = (job.time_start - job_requested.time_start).seconds

        context_details = {
            **context_details,
            "runner_name": job.runner_name,
            "runner_public": job.runner_public,
            "repository_private": job.repository_private,
        }

        if time_to_start:
            context_details["time_to_start"] = time_to_start

        # update job from memory
        jobs[job.id] = job

    elif job.action == "completed":
        job_requested = jobs.get(job.id)
        if not job_requested:
            app.logger.warning(f"Job {job.id} is {job.action} but not stored!")
            time_to_finish = 0
        else:
            time_to_finish = (job.time_completed - job.time_start).seconds
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


@scheduler.task("interval", id="monitor_jobs", seconds=15)
def monitor_jobs():
    with scheduler.app.app_context():
        queued_nodes = [job.node_id for job in job_handler.queued.values()]
        jobs_data = query_jobs(queued_nodes)

        app.logger.info(f"Processing data for jobs {job_handler.queued.keys()}")

        for job_data in jobs_data["nodes"]:
            job = job_handler.queued.get(job_data["id"])
            if (
                job_data.get("checkSuite", {}).get("status") == "COMPLETED"
                or job_data["status"] != "QUEUED"
            ):
                job = job_handler.queued.pop(job_data["id"], None)
                app.logger.info(
                    f"Job {job_data['id']} is no longer queued {job_data['status']}"
                )
                if job:
                    job.status = job_data["status"].lower()
                    job.in_progress_at = parse_datetime(job_data["startedAt"])
                    job.completed_at = parse_datetime(job_data["completedAt"])
                    job.final_queued_time_updated = True
            if job:
                app.logger.info(
                    f"Sending metric for {job_data['id']} with status {job_data['status']},"
                    f"duration {job.seconds_in_queue}"
                )
                job.send_queued_metric()
            else:
                app.logger.info(f"No job for {job_data['id']}")


@scheduler.task("interval", id="monitor_queued", seconds=30)
def monitor_queued_jobs():
    """Return the job that has been queued and not starting for long time."""
    app.logger.debug("Starting monitor_queued_jobs")

    if not jobs:
        return

    queued_jobs = [job for job in jobs.values() if job.action == "queued"]
    if not queued_jobs:
        return

    job = min(queued_jobs, key=lambda x: x.time_start)
    delay = (datetime.now() - job.time_start).seconds

    if delay <= int(os.getenv("QUEUED_JOBS_DELAY_THRESHOLD", 150)):
        return

    context_details = {
        "action": "monitor_queued",
        "job_id": job.id,
        "job_name": job.name,
        "repository": job.repository,
        "started_at": job.time_start,
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
