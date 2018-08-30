FROM python:3.6
WORKDIR /usr/src/app
RUN apt-get update && \
    apt-get -y install libnss-wrapper gettext
COPY . .
RUN pip install pipenv && \
    pipenv install --system --deploy
RUN mkdir /.ssh && \
    ssh-keyscan -t rsa github.com >> /.ssh/known_hosts
USER 1001
CMD ["service.sh"]
