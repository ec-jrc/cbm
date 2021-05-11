# Jupyter Notebook Tensorflow Python Stack for Copernicus DIAS

__This will be needed only if the jupyter platform is not preinstalled by the DIAS service provider__

## Jupyter server

The Jupyter Server is an open source web application that allows to create and share documents that contain live code, equations, visualizations and narrative text. Uses include: data cleaning and transformation, numerical simulation, statistical modeling, data visualization, machine learning, and much more (https://jupyter.org). JupyterLab is the next-generation user interface for Project Jupyter offering all the familiar building blocks of the classic Jupyter Notebook (notebook, terminal, text editor, file browser, rich outputs, etc.) in a flexible and powerful user interface. JupyterLab will eventually replace the classic Jupyter Notebook (https://jupyterlab.readthedocs.io).

**Instaling DIAS Jupyter (Jupyter Notebook Tensorflow Python Stack for CbM)**

GTCAP cbm_jupyter docker image is based on the tensorflow-notebook of Jupyter Notebook Scientific Python Stack and configured for Copernicus DIAS for CAP “checks by monitoring” with all the requirements. This is the recommended way to run a Jupyter server. Some DIAS providers may provide preinstalled Jupyter environments as well.

**Run GTCAP Jupyter docker image**

To run a jupyter server with the default setup:
```
docker run -p 8888:8888 gtcap/cbm_jupyter
```
This will run the jupyter server on port '8888' and can be accessed from a web browser on 'localhost:8888'.

To expose the jupyter server to port 80, change -p 8888:8888 to -p 80:8888, or to any other port.


### More options

To pull the docker image from [dockerhub](https://hub.docker.com/r/gtcap/cbm_jupyter) use:
```sh
docker pull gtcap/cbm_jupyter
```

To configure and access the current local directory within the jupyter server run:
```
docker run -it --privileged=true --user root -e NB_USER="$USER" -e NB_UID="$UID" -e NB_GID="$UID" -p 8888:8888 -v "$PWD":/home/"$USER" --name=jupyter4cbm gtcap_jupyter
```
<!-- $ -->

To run the Jupyter server with a predefined token, add at the end of the command:
```
start-notebook.sh --NotebookApp.token='abcdefghijk1234567890'
```

**Note**: JupyterLab can be accessed by adding /lab at the url, instead of /tree (e.g. localhost/lab).
To run with enabled JupyterLab by default add -e JUPYTER_ENABLE_LAB=yes flag e.g.:
```sh
docker run -it --privileged=true --user root -e NB_USER="$USER" -e NB_UID="$UID" -e NB_GID="$UID" -e JUPYTER_ENABLE_LAB=yes -p 8888:8888 -v "$PWD":/home/"$USER" --name=jupyter4cbm gtcap/cbm_jupyter
```
For more options visit [jupyter-docker-stacks.readthedocs.io](https://jupyter-docker-stacks.readthedocs.io/en/latest)

To access jupyter server, open in the web browser the link with the token that is provided in the terminal (e.g. http://localhost/tree?token=abcdefghijk1234567890).

**Usage Instructions**

All Jupyter Notebooks files have the extension '.ipynb' and are identifiable by the notebook icon next to their name.
To create a new notebook in JupyterLab, go to File -> New and select 'New Notebook'.
Notebooks currently running will have a green dot, while non-running ones will not.
To run a cell with a script, click on the run icon or press Shift+Enter

More information can be found at: https://jupyter.org/documentation

**To build GTCAP Jupyter docker image from source**

In the folder "docker/gtcap_jupyter/" there is a "Dockerfile" to create a Jupyter docker image.
To create the "gtcap_jupyter" docker image from source run:

```sh
git clone https://github.com/ec-jrc/cbm.git
cd docker/cbm_jupyter
docker build -t gtcap/cbm_jupyter .
```
