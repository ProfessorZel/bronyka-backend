# pull official base image
FROM python:3.13-slim-bookworm
# set working directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update \
  && apt-get -y install gcc \
  && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# add app
COPY . .
ENV DATABASE_URL sqlite+aiosqlite:///./data/fastapi.db
ENV TZ Europe/Moscow
ENV AUTH_TOKEN_LIFETIME_SECONDS 86400
ENV DENY_CANCEL_AFTER_MINUTES_USED 10
ENV BACKDATE_RESERVATION_ALLOWED_SECONDS 300
ENV MAX_RESERVATION_DURATION_MINUTES 1440
CMD sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"
