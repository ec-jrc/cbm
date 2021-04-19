FROM tiangolo/meinheld-gunicorn-flask

MAINTAINER JRC UNIT D5

COPY ./requirements.txt /app/
WORKDIR /app

RUN apt-get update
RUN apt-get install -y python-numpy gdal-bin libgdal-dev gcc nano
RUN apt-get clean

RUN export CPLUS_INCLUDE_PATH=/usr/include/gdal
RUN export C_INCLUDE_PATH=/usr/include/gdal

RUN pip3 install --upgrade pip
RUN pip3 install --user -r requirements.txt
