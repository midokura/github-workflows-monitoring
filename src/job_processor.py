def extract_jobs_metrics_from_data(jobs_data: dict, queued_node_ids_set: set):
    jobs_metrics = []

    for job in jobs_data["nodes"]:

        if job["status"] != "QUEUED":
            queued_node_ids_set.discard(job["id"])
            continue

        context_details = {
            "action": "monitor_queued",
            "job_id": job["id"],
            "job_name": job["name"],
            "status": job["status"],
            "started_at": job["startedAt"],
            "completed_at": job["completedAt"],
            }

        jobs_metrics.append(context_details)
    return jobs_metrics
