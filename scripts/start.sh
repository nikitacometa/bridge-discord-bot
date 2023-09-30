#!/bin/sh

docker-compose up -d "$@" && scripts/log.sh
