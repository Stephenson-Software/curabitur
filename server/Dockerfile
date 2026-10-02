FROM ubuntu:24.04

RUN apt-get update && apt-get install -y python3

COPY . /app-server

WORKDIR /app-server
CMD ["python3","src/chatServer.py"]