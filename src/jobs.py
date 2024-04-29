from github import GithubJob


class Job:
    def __init__(self, github_job: GithubJob) -> None:
        self.github_job = github_job


class JobEventsHandler:
    def __init__(self) -> None:
        self.queued = dict()
        self.in_progress = dict()

    def process_event(self, event: dict):
        status = event["action"]

        if status == "queued":
            self._process_queued_event(event)

        elif status == "in_progress":
            self._process_in_progress_event(event)

        elif status == "completed":
            self._process_completed_event(event)

        else:
            pass

    def _get_event_job_id(self, event: dict):
        return event["workflow_job"]["id"]

    def _create_job(self, githubJob: GithubJob) -> Job:
        return Job(github_job=githubJob)

    def _process_queued_event(self, event: dict):
        job = self._create_job(GithubJob(event))
        self.queued[self._get_event_job_id(event)] = job

    def _process_in_progress_event(self, event: dict):
        job_id = self._get_event_job_id(event)
        job = self.queued.pop(job_id, None)

        if not job:
            job = self._create_job(GithubJob(event))
        else:
            # Update github job event from job
            job.github_job = GithubJob(event)

        self.in_progress[job_id] = job

        # TODO send final time in queue

    def _process_completed_event(self, event: dict):
        job_id = self._get_event_job_id(event)
        self.in_progress.pop(job_id, None)

        # TODO send final time in progress
