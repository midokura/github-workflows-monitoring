from datetime import datetime


def extract_jobs_metrics_from_data(jobs_data: dict, queued_node_ids: dict):
    jobs_metrics = []

    for job in jobs_data["nodes"]:
        started_at = datetime.strptime(job["startedAt"], "%Y-%m-%dT%H:%M:%SZ")
        now = datetime.now()

        context_details = {
            "action": "monitor_queued",
            "job_id": job["id"],
            "job_name": job["name"],
            "is_public": queued_node_ids[job["id"]].runner_public,
            "runner_name": queued_node_ids[job["id"]].runner_name,
            "seconds_in_queue": (now - started_at).total_seconds(),
            }

        jobs_metrics.append(context_details)

        if job["status"] != "QUEUED":
            queued_node_ids.pop(job["id"], None)
            continue

    return jobs_metrics
