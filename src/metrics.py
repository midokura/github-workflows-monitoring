import logging
import re

from datadog import initialize, statsd
from flask import current_app

options = {
    "statsd_host": "datadog-agent.datadog.svc.cluster.local",
    "statsd_port": 8125,
}

initialize(**options)

logger = logging.getLogger(__name__)


TAG_INVALID_CHARS_RE = re.compile(r"[^\w\d_\-:/\.]", re.UNICODE)
TAG_INVALID_CHARS_SUBS = "_"


def normalize_tags(tag_list):
    return [TAG_INVALID_CHARS_RE.sub(TAG_INVALID_CHARS_SUBS, tag) for tag in tag_list]


def send_queued_job(
    seconds_in_queue: int,
    job_name: str,
    status: str,
    repository: str,
    public: bool,
    buildjet: bool,
    runner_group_name: str,
):
    tags = [
        f"repository:{repository}",
        f"job_name:{job_name}",
        f"status:{status}",
        f"public:{public}",
        f"buildjet:{buildjet}",
        f"runner_group_name:{runner_group_name}",
    ]

    tags = normalize_tags(tags)

    current_app.logger.info(f"Sending {seconds_in_queue} tags {tags}")

    statsd.distribution(
        "midokura.github_runners.jobs.seconds_in_queue.distribution",
        seconds_in_queue,
        tags=tags,
    )
