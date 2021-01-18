FROM thinkwhere/gdal-python:latest

LABEL maintainer="Guido Lemoine"\
      organisation="EC-JRC"\
      version="1.0"\
      release-date="2019-03-18"\
      description="DIAS python3 essentials"

WORKDIR /usr/src/app

# Update base container install
RUN apt-get update --fix-missing
RUN apt-get upgrade -y

RUN apt-get install -y libxml2-dev libxslt-dev vim
RUN apt-get -y autoremove

RUN pip install --upgrade pip

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt