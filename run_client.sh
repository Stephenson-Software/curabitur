# /bin/bash

if [ $# -eq 0 ]
  then
    echo "Usage: ./run.sh <server-ip>"
    exit 1
fi

echo "Building client image..."
docker build ./client -t chat-client

echo "Running client..."
docker run -e CHAT_SERVER_IP=$1 -it --rm chat-client
