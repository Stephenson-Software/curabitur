FROM ubuntu:24.04

RUN apt-get update && apt-get install -y python3

COPY . /app-client

WORKDIR /app-client
CMD ["python3","src/chatClient.py"]