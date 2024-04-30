from datadog import initialize, statsd

from flask import current_app

options = {
    "statsd_host": "datadog-agent.datadog.svc.cluster.local",
    "statsd_port": 8125,
}

initialize(**options)


def send_queued_job(
    seconds_in_queue: int,
    job_name: str,
    job_id,
    repository: str,
    runner: str,
    run_id: str,
    public: bool,
):
    tags = [
        f"job:{job_name}",
        f"repository:{repository}",
        f"runner_name:{runner}",
        f"public:{public}",
    ]
    current_app.logger.info(
        f"Submitting queue metric time: {seconds_in_queue}, tags: {tags}"
    )
    statsd.histogram(
        "midokura.github_runners.jobs.seconds_in_queue.histogram",
        seconds_in_queue,
        tags=tags,
    )
