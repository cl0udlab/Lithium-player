FROM python:3.12-bookworm as build

RUN pip install poetry==1.8.5

WORKDIR /app
COPY ./src/ .
RUN poetry install
