FROM friendexing_web:latest
RUN pip install prospector[with_vulture,with_mypy,with_bandit]
WORKDIR /opt/qafriendexing
