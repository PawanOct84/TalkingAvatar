# Dockerfile

# pull the official docker image
FROM python:3.10

VOLUME ["/container-data"]
# MAINTAINER Toonist
LABEL Remarks="This is a dockerfile example for Python 3.10 system"
RUN useradd -ms /bin/bash fastApiUser

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# set work directory
WORKDIR /app

# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1-mesa-glx \
        ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# install dependencies
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8000

# copy project
COPY . .
