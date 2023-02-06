# github-workflows-monitoring

[![Tests](https://github.com/midokura/github-workflows-monitoring/actions/workflows/tests.yaml/badge.svg)](https://github.com/midokura/github-workflows-monitoring/actions/workflows/tests.yaml)

## About

Github Workflow Monitoring is a small Flask-based web server that connects to Github using websockets to monitor Github Actions workflows. It tracks each workflow's state (queued, in_progress, completed) and calculates the time spent in each state. The metrics are logged in logfmt format for easy consumption by Grafana.

## Testing

Into a virtual environment, install the requirements:

    pip install -r tests/requirements.txt


To run the tests:

    pytest --cov=src
