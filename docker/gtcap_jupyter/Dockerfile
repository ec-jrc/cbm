# Authors: Guido Lemoine, Konstantinos Anastasakis

FROM jupyter/tensorflow-notebook

USER root

RUN apt-get update -q
RUN apt-get upgrade -y
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:ubuntugis/ubuntugis-unstable && apt-get update
RUN apt-get install -y \
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
    libgdal-dev

RUN export CPLUS_INCLUDE_PATH=/usr/include/gdal
RUN export C_INCLUDE_PATH=/usr/include/gdal

RUN pip install --upgrade pip

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

RUN pip install GDAL==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal"

USER jovyan