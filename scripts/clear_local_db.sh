#!/usr/bin/env bash

source .env

mongo "localhost:${MONGODB_PORT}/bridge-bot" --eval "db.dropDatabase()"
