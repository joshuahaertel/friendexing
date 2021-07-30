FROM python:alpine as base
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/friendexing
COPY requirements.txt .
RUN apk add gcc musl-dev libffi-dev g++ cargo openssl-dev
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# DOCKER_BUILDKIT=1 docker build --target web . -t friendexing_web
FROM base as web
WORKDIR /opt/friendexing/friendexing

# DOCKER_BUILDKIT=1 docker build --target coverage . -t friendexing_coverage
FROM web as coverage
RUN pip install coverage
COPY report_coverage.sh /opt/friendexing/

# DOCKER_BUILDKIT=1 docker build --target test . -t friendexing_test
FROM python:alpine as test
ENV PYTHONUNBUFFERED=1
RUN pip install --upgrade pip
RUN pip install selenium coverage
RUN apk add chromium chromium-chromedriver firefox
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.29.0/geckodriver-v0.29.0-linux64.tar.gz
RUN tar -zxf geckodriver-v0.29.0-linux64.tar.gz -C /usr/bin
WORKDIR /opt/friendexing/tests

# DOCKER_BUILDKIT=1 docker build --target lint . -t friendexing_lint
FROM base as lint
RUN pip install prospector[with_vulture,with_mypy,with_bandit] selenium django-stubs
WORKDIR /opt/friendexing
