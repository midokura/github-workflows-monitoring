from unittest.mock import patch
import pytest
import app
from app import monitor_jobs
from github import GithubJob
from jobs import Job, JobEventsHandler


@pytest.fixture
def queued_job():
    return Job(
        GithubJob(
            {
                "workflow_job": {
                    "id": "workflow_id_queued",
                    "name": "workflow name",
                    "run_id": 1234567890,
                    "started_at": "2024-04-29T12:43:16Z",
                    "completed_at": None,
                    "node_id": "CR_queued_1234",
                    "runner_name": "test runner",
                    "runner_group_name": "Runner Group Test",
                    "labels": ["self-hosted"],
                },
                "repository": {"full_name": "test/repo"},
                "action": "queued",
            }
        )
    )


@pytest.fixture
def in_progress_job():
    return Job(
        GithubJob(
            {
                "workflow_job": {
                    "id": "workflow_id_in_progress",
                    "name": "workflow name",
                    "run_id": 1234567890,
                    "started_at": "2024-04-29T12:43:16Z",
                    "completed_at": None,
                    "node_id": "CR_in_progress_1234",
                    "runner_name": "test runner",
                    "runner_group_name": "Runner Group Test",
                    "labels": ["self-hosted"],
                },
                "repository": {"full_name": "test/repo"},
                "action": "queued",
            }
        )
    )


@patch("jobs.Job.send_queued_metric")
@patch("app.query_jobs")
def test_monitor_jobs(
    query_jobs_mock, send_queued_metric_mock, queued_job, in_progress_job
):
    app.job_handler = JobEventsHandler()
    app.job_handler.queued = {
        "workflow_id_queued": queued_job,
        "workflow_id_in_progress": in_progress_job,
    }

    query_jobs_mock.return_value = {
        "nodes": [
            {
                "id": "workflow_id_queued",
                "status": "QUEUED",
                "checkSuit": {"status": "IN_PROGRESS"},
                "startedAt": "2024-04-29T12:43:16Z",
                "completedAt": None,
            },
            {
                "id": "workflow_id_in_progress",
                "status": "IN_PROGRESS",
                "checkSuit": {"status": "IN_PROGRESS"},
                "startedAt": "2024-04-29T12:43:32Z",
                "completedAt": None,
            },
        ]
    }

    monitor_jobs()

    assert "workflow_id_in_progress" not in app.job_handler.queued
    assert in_progress_job.status == "in_progress"
    assert in_progress_job.in_progress_at is not None
    send_queued_metric_mock.assert_called()


@patch("jobs.Job.send_queued_metric")
@patch("app.query_jobs")
def test_monitor_jobs_completed_suit(
    query_jobs_mock, send_queued_metric_mock, queued_job
):
    app.job_handler = JobEventsHandler()
    app.job_handler.queued = {
        "workflow_id_queued": queued_job,
    }

    query_jobs_mock.return_value = {
        "nodes": [
            {
                "id": "workflow_id_queued",
                "status": "QUEUED",
                "checkSuit": {"status": "COMPLETED"},
                "startedAt": "2024-04-29T12:43:16Z",
                "completedAt": None,
            }
        ]
    }

    monitor_jobs()

    assert "workflow_id_queued" not in app.job_handler.queued
    send_queued_metric_mock.assert_called()
