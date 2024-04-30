import logging
from logging.config import dictConfig
from datadog import initialize, statsd

from const import LOGGING_CONFIG

options = {
    "statsd_host": "datadog-agent.datadog.svc.cluster.local",
    "statsd_port": 8125,
}

initialize(**options)

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("werkzeug")


def send_queued_job(
    seconds_in_queue: int,
    job_name: str,
    status: str,
    job_labels: str,
    repository: str,
    public: bool,
    runner_group_name: str,
):
    tags = [
        f"job:{job_name}",
        f"repository:{repository}",
        f"status:{status}",
        f"labels:{job_labels}",
        f"public:{public}",
        f"runner_group_name:{runner_group_name}",
    ]
    logger.info(f"Submitting queue metric time: {seconds_in_queue}, tags: {tags}")
    statsd.histogram(
        "midokura.github_runners.jobs.seconds_in_queue.histogram",
        seconds_in_queue,
        tags=tags,
    )
