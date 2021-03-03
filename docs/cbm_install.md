# Installation

## Dependencies

The 'cbm' python library has one C library dependency: GDAL >=2.x. GDAL itself depends on many of other libraries provided by most major operating systems and also depends on the non standard GEOS and PROJ4 libraries.

For GDAL installation see: [pypi.org/project/GDAL](https://pypi.org/project/GDAL/).

## Installing from [PyPI](https://pypi.org/project/cbm/)

```bash
pip install cbm
```

## Installing from source:

```bash
git clone https://github.com/ec-jrc/cbm.git
cd cbm
python setup.py install
```

## Installing for development

```bash
git clone https://github.com/ec-jrc/cbm.git
cd cbm
pip install -e .
```
