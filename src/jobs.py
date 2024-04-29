from datetime import datetime
from github import GithubJob


class Job:
    def __init__(self, github_job: GithubJob) -> None:
        self.github_job: GithubJob = None
        self.stauts: str = None

        self.queued_at: datetime = None
        self.in_progress_at: datetime = None
        self.completed_at: datetime = None

        self._update_attributes(github_job)

        self.node_id = self.github_job.node_id

    def _update_attributes(self, github_job: GithubJob):
        self.github_job: GithubJob = github_job
        self.status = github_job.action

        if self.github_job.action == "queued":
            self.queued_at = self.github_job.time_start

        if (
            self.github_job.action == "in_progress"
            or self.github_job.action == "completed"
        ):
            self.in_progress_at = self.github_job.time_start
            self.completed_at = self.github_job.time_completed

    def update(self, github_job: GithubJob):
        self._update_attributes(github_job)


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
            job.update(GithubJob(event))

        self.in_progress[job_id] = job

        # TODO send final time in queue

    def _process_completed_event(self, event: dict):
        job_id = self._get_event_job_id(event)
        self.in_progress.pop(job_id, None)

        # TODO send final time in progress
