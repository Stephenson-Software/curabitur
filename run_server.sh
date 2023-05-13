# /bin/bash

echo "Building server image..."
docker build ./server -t chat-server

echo "Running server..."
docker run -it --rm chat-server