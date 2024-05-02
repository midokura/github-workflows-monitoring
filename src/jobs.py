from flask import current_app
import metrics

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
        self.labels = "-".join(sorted(self.github_job.labels))
        self.final_queued_time_updated = False

    @property
    def seconds_in_queue(self):
        if self.status == "queued":
            return (datetime.now() - self.queued_at).total_seconds()

        if self.status == "in_progress" or self.status == "completed":
            return (self.in_progress_at - self.queued_at).total_seconds()

    def _update_attributes(self, github_job: GithubJob):
        self.github_job: GithubJob = github_job
        self.status = self.github_job.action

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

    def send_queued_metric(self):
        current_app.logger.info("Sending queued metric")
        metrics.send_queued_job(
            seconds_in_queue=self.seconds_in_queue,
            job_name=self.github_job.job_name,
            status=self.status,
            job_labels=self.labels,
            repository=self.github_job.repository,
            runner_group_name=self.github_job.runner_group_name,
            public=self.github_job.runner_public,
        )


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
        return event["workflow_job"]["node_id"]

    def _create_job(self, githubJob: GithubJob) -> Job:
        return Job(github_job=githubJob)

    def _process_queued_event(self, event: dict):
        job = self._create_job(GithubJob(event))
        self.queued[self._get_event_job_id(event)] = job

    def _process_in_progress_event(self, event: dict):
        job_id = self._get_event_job_id(event)
        job = self.queued.get(job_id, None)

        if not job:
            job = self._create_job(GithubJob(event))
        else:
            job.update(GithubJob(event))
            # This is a fallover in case the job was not processed during the tracking time.
            # if not job.final_queued_time_updated:
            # job.final_queued_time_updated = True
            # job.send_queued_metric()

        # self.in_progress[job_id] = job

    def _process_completed_event(self, event: dict):
        job_id = self._get_event_job_id(event)
        self.in_progress.pop(job_id, None)

        # TODO send final time in progress
