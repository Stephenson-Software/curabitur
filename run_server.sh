#!/bin/bash

echo "Building server image..."
docker build ./server -t chat-server

echo "Running server..."
docker run -e TRACE_USAGE_REPORTING -e DO_NOT_TRACK -it --rm chat-server