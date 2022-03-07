FROM python:3.10.0-bullseye
LABEL maintainer="hello@lutoma.org"
ENV PYTHONUNBUFFERED 1
ARG FONTAWESOME_AUTH_TOKEN

WORKDIR /app

RUN curl -sS https://dl.cloudsmith.io/public/caddy/stable/gpg.key | apt-key add - && \
  echo "deb https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" | tee /etc/apt/sources.list.d/caddy.list

RUN apt-get update && apt-get -y install supervisor build-essential yarnpkg caddy rrdtool librrd8 librrd-dev
RUN pip install --no-cache-dir poetry

COPY pyproject.toml .
COPY poetry.lock .

RUN poetry install && \
  poetry run pip install gunicorn

COPY package.json .
COPY yarn.lock .

# For fontawesome pro
# FIXME should be arg
COPY .npmrc .

RUN yarnpkg install
COPY . .

RUN yarnpkg run gulp build
RUN poetry run ./manage.py collectstatic --noinput

RUN mkdir -p /data
RUN rm -f autopeer/settings_local.py && ln -s /data/settings_local.py autopeer/settings_local.py

HEALTHCHECK CMD curl --fail --unix-socket /run/gunicorn.sock http://localhost || exit 1
CMD ["/usr/bin/supervisord", "-c", "/app/docker/supervisord.conf"]
