# docker build -f Dockerfile . -t friendexing:latest
FROM python:alpine
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/friendexing
COPY requirements.txt .
RUN apk add gcc musl-dev libffi-dev g++
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
