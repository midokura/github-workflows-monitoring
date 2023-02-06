# github-workflows-monitoring


## About

Github Workflow Monitoring is a small Flask-based web server that connects to Github using websockets to monitor Github Actions workflows. It tracks each workflow's state (triggered, in_progress, completed) and calculates the time spent in each state. The metrics are logged in logfmt format for easy consumption by a Grafana instance. The server is easy to set up and use, simply run the server and configure it to connect to your Github repository.


## Testing

Into a virtual environment, install the requirements:

    pip install -r requirements.txt


To run the tests:

    pytest --cov=src
