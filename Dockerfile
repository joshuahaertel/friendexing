FROM python:alpine as base
ENV PYTHONUNBUFFERED=1
WORKDIR /opt/friendexing
COPY requirements.txt .
RUN apk add gcc musl-dev libffi-dev g++ cargo openssl-dev zlib-dev jpeg-dev
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# DOCKER_BUILDKIT=1 docker build --target web . -t friendexing_web
FROM base as web
WORKDIR /opt/friendexing/friendexing

# DOCKER_BUILDKIT=1 docker build --target heroku . -t registry.heroku.com/friendexing/web
#   if necessary, login:
#     heroku login
#     heroku container:login
# docker push registry.heroku.com/friendexing/web
#   This does not work with staged builds:
#     heroku container:push web
# heroku container:release web -a friendexing
FROM web as heroku
RUN apk add curl
RUN pip install whitenoise[brotli]
COPY friendexing/ /opt/friendexing/friendexing/
ENV DJANGO_SETTINGS_MODULE=configuration.settings.heroku
RUN SECRET_KEY=jk REDIS_TLS_URL= python manage.py collectstatic
CMD python manage.py runserver 0.0.0.0:${PORT}

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
