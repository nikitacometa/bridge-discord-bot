FROM python:3.10.13-alpine

COPY . /app
WORKDIR /app

RUN pip install pipenv
RUN pipenv install --deploy
