FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye

COPY requirements_test.txt /tmp/requirements_test.txt

RUN pip install --no-cache-dir ruff black -r /tmp/requirements_test.txt
