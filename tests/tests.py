from src.const import GithubHeaders

HEADERS = {
    GithubHeaders.EVENT.value: "workflow_job",
    "Content-Type": "application/json",
    "User-Agent": "GitHub-Hookshot/123",
}
BODY = {
    "action": "",
    "workflow_job": {
        "id": 0,
        "run_id": 10,
        "workflow_name": "CI",
        "head_branch": "new-feature-branch",
        "started_at": "2023-01-27T14:00:00Z",
        "conclusion": None,
        "labels": [],
        "runner_id": None,
        "runner_name": None,
        "runner_group_id": None,
        "runner_group_name": None,
        "name": "Build",
    },
    "repository": {
        "name": "foo",
        "full_name": "foo/foo",
        "private": False,
    },
    "sender": {
        "login": "testerbot",
        "id": 1,
        "type": "User",
    },
}


def test_method_not_allowed(client):
    assert client.get("/github-webhook").status_code == 401


def test_headers_not_correct(client, caplog):
    response = client.post("/github-webhook", headers={'User-Agent': 'foo'})
    assert response.status_code == 401
    assert caplog.messages == [
        "User-Agent is foo",
        "Content is not JSON",
        "No GitHub Event received!",
    ]


def test_no_body_bad_request(client):
    response = client.post("/github-webhook", headers=HEADERS)
    assert response.status_code == 400


def test_unknown_event(client, caplog):
    headers = HEADERS.copy()
    headers[GithubHeaders.EVENT.value] = "foo"
    response = client.post("/github-webhook", headers=headers, json={})
    assert response.status_code == 405
    assert caplog.messages == ["Unknown event type foo, can't handle"]


def test_started_job_not_stored(client, caplog):
    body_started = BODY.copy()
    body_started["action"] = "in_progress"
    body_started["workflow_job"]["id"] = 2
    response = client.post("/github-webhook", headers=HEADERS, json=body_started)
    assert response.status_code == 200
    assert caplog.messages == [
        "Job 2 is in_progress but not stored!",
        "action=in_progress repository=foo/foo branch=new-feature-branch job_id=2 run_id=10 "
        "job_name=Build workflow=CI requestor=testerbot runner_name= runner_public=false "
        "repository_private=false",
    ]


def test_finished_job_not_stored(client, caplog):
    body_finished = BODY.copy()
    body_finished["action"] = "completed"
    body_finished["workflow_job"]["id"] = 3
    response = client.post("/github-webhook", headers=HEADERS, json=body_finished)
    assert response.status_code == 200
    assert caplog.messages == [
        "Job 3 is completed but not stored!",
        "action=completed repository=foo/foo branch=new-feature-branch job_id=3 run_id=10 "
        "job_name=Build workflow=CI requestor=testerbot runner_name= time_to_finish=0 conclusion=",
    ]


def test_unknown_action(client, caplog):
    body_started = BODY.copy()
    body_started["action"] = "queued"
    body_started["workflow_job"]["id"] = 4
    response = client.post("/github-webhook", headers=HEADERS, json=body_started)
    body_failed = body_started.copy()
    body_failed["action"] = "failed"
    response = client.post("/github-webhook", headers=HEADERS, json=body_failed)
    assert response.status_code == 200
    assert caplog.messages == [
        "action=queued repository=foo/foo branch=new-feature-branch job_id=4 run_id=10 "
        "job_name=Build workflow=CI requestor=testerbot",
        "Unknown action failed, removing from memory",
    ]


def test_queued_job(client, caplog):
    body_queued = BODY.copy()
    body_queued["action"] = "queued"
    body_queued["workflow_job"]["id"] = 1
    response = client.post("/github-webhook", headers=HEADERS, json=body_queued)
    assert response.status_code == 200
    assert caplog.messages == [
        "action=queued repository=foo/foo branch=new-feature-branch job_id=1 run_id=10 "
        "job_name=Build workflow=CI requestor=testerbot"
    ]


def test_logging_flow(client, caplog):
    body_queued = BODY.copy()
    body_queued["action"] = "queued"
    body_queued["workflow_job"]["id"] = 5

    response = client.post("/github-webhook", headers=HEADERS, json=body_queued)
    assert response.status_code == 200
    assert (
        caplog.messages[0]
        == "action=queued repository=foo/foo branch=new-feature-branch job_id=5 run_id=10 "
        "job_name=Build workflow=CI requestor=testerbot"
    )

    body_started = BODY.copy()
    body_started["action"] = "in_progress"
    body_started["workflow_job"]["started_at"] = "2023-01-27T14:00:05Z"
    response = client.post("/github-webhook", headers=HEADERS, json=body_started)
    assert response.status_code == 200
    assert (
        caplog.messages[1]
        == "action=in_progress repository=foo/foo branch=new-feature-branch job_id=5 run_id=10 "
        "job_name=Build workflow=CI requestor=testerbot runner_name= runner_public=false "
        "repository_private=false time_to_start=5"
    )

    body_completed = BODY.copy()
    body_completed["action"] = "completed"
    body_completed["workflow_job"]["conclusion"] = "success"
    body_completed["workflow_job"]["completed_at"] = "2023-01-27T14:05:00Z"
    response = client.post("/github-webhook", headers=HEADERS, json=body_completed)
    assert response.status_code == 200
    assert (
        caplog.messages[2]
        == "action=completed repository=foo/foo branch=new-feature-branch job_id=5 run_id=10 "
        "job_name=Build workflow=CI requestor=testerbot runner_name= time_to_finish=295 "
        "conclusion=success"
    )


def test_logging_flow_queued_after_in_progress(client, caplog):
    body_queued = BODY.copy()
    body_queued["action"] = "queued"
    body_queued["workflow_job"]["id"] = 6
    body_queued["workflow_job"]["started_at"] = "2023-02-17T06:57:48Z"

    response = client.post("/github-webhook", headers=HEADERS, json=body_queued)
    assert response.status_code == 200
    assert (
        caplog.messages[0]
        == "action=queued repository=foo/foo branch=new-feature-branch job_id=6 run_id=10 "
        "job_name=Build workflow=CI requestor=testerbot"
    )

    body_started = BODY.copy()
    body_started["action"] = "in_progress"
    body_started["workflow_job"]["started_at"] = "2023-02-17T06:57:46Z"
    response = client.post("/github-webhook", headers=HEADERS, json=body_started)

    assert response.status_code == 200
    assert caplog.messages[1] == "Job 6 was in progress before being queued"
    assert (
        caplog.messages[2]
        == "action=in_progress repository=foo/foo branch=new-feature-branch job_id=6 run_id=10 "
        "job_name=Build workflow=CI requestor=testerbot runner_name= runner_public=false "
        "repository_private=false"
    )
