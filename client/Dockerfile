FROM ubuntu:18.04W

RUN apt-get update && apt-get install -y python3.7 python3-pip

COPY . /app-client

WORKDIR /app-client
CMD ["python3.7", "src/chatClient.py"]