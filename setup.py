from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='cbm',
    version='0.0.3',
    python_requires='>=3.6',
    description='Checks by Monitoring (CbM)',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/ec-jrc/cbm',
    author='Guido Lemoine, Konstantinos Anastasakis',
    author_email='',
    license='BSD 3-clause',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'boto3',
        'botocore',
        'Fiona',
        'ipyleaflet',
        'ipywidgets>=7.6.0',
        'matplotlib',
        'numpy',
        'pandas',
        'psycopg2-binary',
        'rasterio==1.1.5',
        'rasterstats',
        'requests',
        'tqdm',
        'gdal',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
    ],
)
