FROM tiangolo/meinheld-gunicorn-flask

MAINTAINER Konstantinos Anastasakis

COPY ./requirements.txt /app/
WORKDIR /app

RUN apt-get update
RUN apt-get install -y nano
RUN pip3 install --upgrade pip
RUN pip3 install --user -r requirements.txt
