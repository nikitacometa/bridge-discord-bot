FROM python:3.10.13-alpine

COPY . /bot
WORKDIR /bot

RUN pip install pipenv
RUN pipenv install --deploy
