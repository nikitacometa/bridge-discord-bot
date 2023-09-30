#!/bin/sh

DIR_NAME=$(basename "$PWD")
IMAGE_NAME="${DIR_NAME}_app_1"

docker logs "${IMAGE_NAME}" -f
