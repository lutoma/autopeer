FROM python:3.10.2-slim-bullseye
LABEL maintainer="hello@lutoma.org"
ENV PYTHONUNBUFFERED 1
ARG FONTAWESOME_AUTH_TOKEN

WORKDIR /app

RUN apt-get update && apt-get -y --no-install-recommends install curl gnupg2
RUN curl -sS https://dl.cloudsmith.io/public/caddy/stable/gpg.key | apt-key add - && \
  echo "deb https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" | tee /etc/apt/sources.list.d/caddy.list

RUN apt-get update && apt-get -y --no-install-recommends install gcc libc6-dev supervisor yarnpkg caddy rrdtool librrd8 librrd-dev whois wireguard-tools gettext git
RUN pip install --no-cache-dir poetry

COPY pyproject.toml .
COPY poetry.lock .

RUN poetry install && \
  poetry run pip install gunicorn psycopg2-binary

COPY package.json .
COPY yarn.lock .
COPY .npmrc .

RUN yarnpkg install
COPY . .

RUN yarnpkg run gulp build
RUN poetry run ./manage.py collectstatic --noinput
RUN poetry run ./manage.py compilemessages

# Clean up build dependencies
RUN apt-get remove -y curl gnupg2 gcc libc6-dev yarnpkg librrd-dev gettext git && \
  apt-get -y autoremove && \
  rm -rf node_modules

RUN mkdir -p /data
RUN rm -f autopeer/settings_local.py && \
  ln -s /data/settings_local.py autopeer/settings_local.py && \
  ln -s /data/ssh $HOME/.ssh

HEALTHCHECK CMD curl --fail --unix-socket /run/gunicorn.sock http://localhost || exit 1
CMD ["/usr/bin/supervisord", "-c", "/app/docker/supervisord.conf"]
