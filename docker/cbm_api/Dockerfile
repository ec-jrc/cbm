FROM python:3.8-slim-buster
MAINTAINER JRC UNIT D5

COPY ./requirements.txt /app/
WORKDIR /app

RUN apt-get update \
    && apt-get install -y gcc nano\
    && apt-get clean

RUN pip install --upgrade pip
RUN pip install --user -r requirements.txt

EXPOSE 5000
CMD python app.py
