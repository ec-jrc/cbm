# Installation

## Dependencies

The 'cbm' python library has one C library dependency: GDAL >=2.x. GDAL itself depends on many of other libraries provided by most major operating systems and also depends on the non standard GEOS and PROJ4 libraries, see: [Install GDAL](https://jrc-cbm.readthedocs.io/en/latest/cbm_install.html#id1).


## Installing from PyPI

The cbm python library is available at the [Python Package Index](https://pypi.org/project/cbm) software repository.

Can be instaled with:

```bash
pip3 install cbm
```

To upgrade use the -U flag

```bash
pip3 install cbm -U
```

## Installing for development

For development install cbm in [editable mode](https://pip.pypa.io/en/stable/reference/pip_install/#cmdoption-e) with:

```bash
git clone https://github.com/ec-jrc/cbm.git
cd cbm
pip3 install -e .
```

To update cbm with the local changes run in the cbm folder:

.. code-block:: bash

    pip3 install -U -f -e .


## Installing from source:

Install from source to get the latest updates (Not editable).

```bash
git clone https://github.com/ec-jrc/cbm.git
cd cbm
python setup.py install
```

## Uninstallation

To uninstall cbm run:

```bash
pip3 uninstall cbm
```


## Install GDAL

Open a terminal window and enter the command to update repositories:

.. code-block:: bash

    sudo apt-get update && sudo apt-get upgrade


To get the add-apt-repository command, install the software-properties-common package:

.. code-block:: bash

    sudo apt-get install software-properties-common


To get the latest GDAL/OGR version, add the PPA to sources, then install the gdal-bin package:

.. code-block:: bash

    sudo add-apt-repository ppa:ubuntugis/ppa


Update your source packages:

.. code-block:: bash

    sudo apt-get update

Install the GDAL/OGR package and other required packages as well:

.. code-block:: bash

    sudo apt-get install -y \
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


Include paths using the environment variables with:

.. code-block:: bash

    export CPLUS_INCLUDE_PATH=/usr/include/gdal
    export C_INCLUDE_PATH=/usr/include/gdal


Then you will be able to istall python gdal with:

.. code-block:: bash

    pip install GDAL==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal"

<!-- $ -->
For more information on GDAL installation see:
[pypi GDAL Installation](https://pypi.org/project/GDAL)
or [How To Install GDAL/OGR Packages on Ubuntu](https://mothergeo-py.readthedocs.io/en/latest/development/how-to/gdal-ubuntu-pkg.html).


## Troubleshooting

In case of permission errors try using 'user' flag:
```python
pip install cbm --user
```

On Windowns GDAL may need to be installed with the [osgeo4w](https://trac.osgeo.org/osgeo4w/) installation package

In some cases the rasterio package may need to be installed with:
```bash
conda install -c conda-forge rasterio=1.1.5
```
