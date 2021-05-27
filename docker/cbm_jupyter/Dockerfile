# Authors: Guido Lemoine, Konstantinos Anastasakis

FROM jupyter/tensorflow-notebook

USER root

RUN apt-get update -q
RUN apt-get upgrade -y
RUN apt-get install -y software-properties-common
RUN apt-get update -q
RUN add-apt-repository ppa:ubuntugis/ppa
RUN apt-get update --fix-missing
RUN apt-get install -y \
    build-essential \
    binutils \
    libproj-dev \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    python3-numpy \
    python3-scipy \
    python3-tk \
    graphviz \
    python3-dev \
    nano \
    g++ \
    gcc \
    libgdal-dev \
    libxml2-dev \
    libxmlsec1-dev

RUN export CPLUS_INCLUDE_PATH=/usr/include/gdal
RUN export C_INCLUDE_PATH=/usr/include/gdal

RUN pip install --upgrade pip
RUN pip install --upgrade pip setuptools wheel
RUN pip install GDAL==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal"

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

EXPOSE 8888

USER jovyan