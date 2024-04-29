from utils import parse_datetime


class GithubJob:
    def __init__(self, json_body: str):
        self.data = json_body

    @property
    def id(self):
        return self.data["workflow_job"]["id"]

    @property
    def job_id(self):
        return self.id

    @property
    def run_id(self):
        return self.data["workflow_job"]["run_id"]

    @property
    def node_id(self):
        return self.data["workflow_job"]["node_id"]

    @property
    def name(self):
        return self.data["workflow_job"]["name"].replace("\n", " ")

    @property
    def job_name(self):
        return self.name

    @property
    def workflow(self):
        return self.data["workflow_job"]["workflow_name"]

    @property
    def time_start(self):
        return parse_datetime(self.data["workflow_job"]["started_at"])

    @property
    def time_completed(self):
        return parse_datetime(self.data["workflow_job"]["completed_at"])

    @property
    def branch(self):
        return self.data["workflow_job"].get("head_branch", "")

    @property
    def repository(self):
        return self.data["repository"]["full_name"]

    @property
    def repository_private(self):
        return self.data["repository"]["private"]

    @property
    def action(self):
        return self.data["action"]

    @property
    def conclusion(self):
        return self.data["workflow_job"].get("conclusion")

    @property
    def requestor(self):
        return self.data.get("sender", {}).get("login")

    @property
    def runner_name(self):
        return self.data["workflow_job"]["runner_name"]

    @property
    def runner_group_name(self):
        return self.data["workflow_job"]["runner_group_name"]

    @property
    def runner_public(self):
        return self.runner_group_name == "GitHub Actions"

    def __str__(self):
        return f"<{self.id}@{self.name}>"
