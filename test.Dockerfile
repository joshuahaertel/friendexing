FROM python:alpine
ENV PYTHONUNBUFFERED=1
RUN pip install --upgrade pip
RUN pip install selenium
RUN apk add chromium chromium-chromedriver
WORKDIR /opt/testfriendexing
