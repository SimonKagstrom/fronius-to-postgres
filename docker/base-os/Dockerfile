FROM python:3-alpine AS fronius-base-os
MAINTAINER Simon Kagstrom <simon.kagstrom@gmail.com>

RUN apk update \
  && apk add --virtual build-deps gcc python3-dev musl-dev \
  && apk add postgresql-dev \
  && pip install psycopg2 \
  && pip install requests \
  && apk del build-deps
