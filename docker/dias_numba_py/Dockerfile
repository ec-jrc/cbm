FROM osgeo/gdal:ubuntu-full-latest

LABEL maintainer="Guido Lemoine"\
      organisation="EC-JRC"\
      version="1.2"\
      release-date="2019-11-12"\
      description="DIAS python3 essentials"

WORKDIR /usr/src/app

RUN apt-get update
RUN apt-get install -y libxml2-dev libxslt-dev gdal-bin sshfs vim python3-pip nano
RUN apt-get -y autoremove
RUN apt-get install ca-certificates

RUN pip install --upgrade pip
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt