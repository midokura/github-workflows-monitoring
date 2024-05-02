import logging
from datadog import initialize, statsd
from flask import current_app

options = {
    "statsd_host": "datadog-agent.datadog.svc.cluster.local",
    "statsd_port": 8125,
}

initialize(**options)

logger = logging.getLogger(__name__)


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
        f"repository:{repository}",
        f"job:{job_name}",
        f"status:{status}",
        # f"labels:{job_labels}",
        # f"public:{public}",
        # f"runner_group_name:{runner_group_name}",
    ]

    current_app.logger.info(f"Sending {seconds_in_queue} tags {tags}")

    statsd.histogram(
        "midokura.github_runners.jobs.seconds_in_queue.histogram",
        seconds_in_queue,
        tags=tags,
    )
