FROM ubuntu:18.04

RUN apt-get update && apt-get install -y python3.7 python3-pip

COPY . /app-server

WORKDIR /app-server
CMD ["python3.7", "src/chatServer.py"]