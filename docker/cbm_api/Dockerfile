FROM tiangolo/meinheld-gunicorn-flask

MAINTAINER Konstantinos Anastasakis

WORKDIR /app

RUN apt-get update
RUN apt-get install -y nano
RUN pip3 install --upgrade pip

COPY ./requirements.txt /app/
RUN pip install --no-cache-dir --upgrade -r requirements.txt
