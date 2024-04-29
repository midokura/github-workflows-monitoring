import pytest

from unittest.mock import Mock

from jobs import JobEventsHandler


@pytest.fixture
def new_job_event():
    return {"workflow_job": {"id": "workflow_id"}, "action": "queued"}


@pytest.fixture
def in_progress_job_event():
    return {"workflow_job": {"id": "workflow_id"}, "action": "in_progress"}


@pytest.fixture
def completed_job_event():
    return {"workflow_job": {"id": "workflow_id"}, "action": "completed"}


def test_new_job(new_job_event):
    handler = JobEventsHandler()

    handler.process_event(new_job_event)

    assert handler.queued.get("workflow_id")


def test_in_progress_job(in_progress_job_event):
    handler = JobEventsHandler()
    job = Mock()
    handler.queued["workflow_id"] = job

    handler.process_event(in_progress_job_event)

    assert not handler.queued.get("workflow_id")
    assert handler.in_progress.get("workflow_id") == job


def test_unprocessed_in_progress_job(in_progress_job_event):
    handler = JobEventsHandler()
    handler.process_event(in_progress_job_event)

    assert handler.in_progress.get("workflow_id")


def test_completed_job(completed_job_event):
    handler = JobEventsHandler()
    handler.in_progress["workflow_id"] = Mock()

    handler.process_event(completed_job_event)

    assert not handler.queued.get("workflow_id")
    assert not handler.in_progress.get("workflow_id")
