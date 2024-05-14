# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.10

FROM scratch AS app
COPY . /dist

FROM python:${PYTHON_VERSION}-slim

RUN --mount=type=bind,from=app,source=/dist,target=/dist,rw \
    pip install --upgrade --no-cache -e /dist && \
    mkdir -p /app && \
    cp -r /dist/src/* /app

WORKDIR /app
EXPOSE 5000
ENTRYPOINT ["flask", "run", "--host", "0.0.0.0"]
