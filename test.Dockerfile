FROM python:alpine
ENV PYTHONUNBUFFERED=1
RUN pip install --upgrade pip
RUN pip install selenium
RUN apk add chromium chromium-chromedriver firefox
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.29.0/geckodriver-v0.29.0-linux64.tar.gz
RUN tar -zxf geckodriver-v0.29.0-linux64.tar.gz -C /usr/bin
WORKDIR /opt/testfriendexing
