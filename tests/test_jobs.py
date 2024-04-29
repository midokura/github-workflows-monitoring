import pytest

from unittest.mock import Mock

from datetime import datetime
from github import GithubJob
from jobs import Job, JobEventsHandler

GITHUB_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@pytest.fixture
def new_job_event():
    return {
        "workflow_job": {
            "id": "workflow_id",
            "started_at": "2024-04-29T12:43:16Z",
            "completed_at": None,
            "node_id": "CR_kwDOHC6jj88AAAAFqGXrPQ",
        },
        "action": "queued",
    }


@pytest.fixture
def in_progress_job_event():
    return {
        "workflow_job": {
            "id": "workflow_id",
            "started_at": "2024-04-29T12:43:32Z",
            "completed_at": None,
            "node_id": "CR_kwDOHC6jj88AAAAFqGXrPQ",
        },
        "action": "in_progress",
    }


@pytest.fixture
def completed_job_event():
    return {
        "workflow_job": {
            "id": "workflow_id",
            "started_at": "2024-04-29T12:43:32Z",
            "completed_at": "2024-04-29T12:45:09Z",
            "node_id": "CR_kwDOHC6jj88AAAAFqGXrPQ",
        },
        "action": "completed",
    }


def test_new_job_event(new_job_event):
    handler = JobEventsHandler()

    handler.process_event(new_job_event)

    assert handler.queued.get("workflow_id")


def test_in_progress_job_event(in_progress_job_event):
    handler = JobEventsHandler()
    job = Mock()
    handler.queued["workflow_id"] = job

    handler.process_event(in_progress_job_event)

    assert not handler.queued.get("workflow_id")
    assert handler.in_progress.get("workflow_id") == job


def test_unprocessed_in_progress_job_event(in_progress_job_event):
    handler = JobEventsHandler()
    handler.process_event(in_progress_job_event)

    assert handler.in_progress.get("workflow_id")


def test_completed_job_event(completed_job_event):
    handler = JobEventsHandler()
    handler.in_progress["workflow_id"] = Mock()

    handler.process_event(completed_job_event)

    assert handler.queued.get("workflow_id") is None
    assert handler.in_progress.get("workflow_id") is None


def test_new_job(new_job_event):
    job = Job(GithubJob(new_job_event))

    assert job.status == "queued"
    assert job.queued_at == datetime.strptime(
        "2024-04-29T12:43:16Z", GITHUB_TIME_FORMAT
    )
    assert job.in_progress_at is None


def test_update_in_progress_job(new_job_event, in_progress_job_event):
    job = Job(GithubJob(new_job_event))
    job.update(GithubJob(in_progress_job_event))

    assert job.status == "in_progress"
    assert job.queued_at == datetime.strptime(
        "2024-04-29T12:43:16Z", GITHUB_TIME_FORMAT
    )
    assert job.in_progress_at == datetime.strptime(
        "2024-04-29T12:43:32Z", GITHUB_TIME_FORMAT
    )
    assert job.completed_at is None


def test_update_completed_job(in_progress_job_event, completed_job_event):
    job = Job(GithubJob(in_progress_job_event))
    job.update(GithubJob(completed_job_event))

    assert job.status == "completed"
    assert job.in_progress_at == datetime.strptime(
        "2024-04-29T12:43:32Z", GITHUB_TIME_FORMAT
    )
    assert job.completed_at == datetime.strptime(
        "2024-04-29T12:45:09Z", GITHUB_TIME_FORMAT
    )
