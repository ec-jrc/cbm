### Jupyter Notebook Tensorflow Python Stack for Copernicus DIAS

__This will be needed only if the jupyter platform is not preinstalled by the DIAS service provider__

The Jupyter Server is an open source web application that allows to create and share documents that contain live code, equations, visualizations and narrative text. Uses include: data cleaning and transformation, numerical simulation, statistical modeling, data visualization, machine learning, and much more (https://jupyter.org). JupyterLab is the next-generation user interface for Project Jupyter offering all the familiar building blocks of the classic Jupyter Notebook (notebook, terminal, text editor, file browser, rich outputs, etc.) in a flexible and powerful user interface. JupyterLab will eventually replace the classic Jupyter Notebook (https://jupyterlab.readthedocs.io).


**Instaling DIAS Jupyter (Jupyter Notebook Tensorflow Python Stack for Copernicus DIAS)**

This is the recommended way to run Jupyter server, it gives more flexibility in terms of installing libraries and other required elements, some DIAS providers may provide preinstalled Jupyter environments as well, but these preinstalled environments may be more difficult to configure.


**Build DIAS Jupyter docker image**

In the folder "jrc-dias/docker/dias_jupyter/" there is a "Dockerfile" to create a Jupyter docker image, this image is based on the tensorflow-notebook of Jupyter Notebook Scientific Python Stack and configured for Copernicus DIAS for CAP “checks by monitoring” with all the requirements.

To create the "dias_jupyter" docker image run in that folder: 

    docker build -t gtcap_jupyter .

After the docker image is created, the docker container must be created. To create the container the current user information is needed.
Get the user id information running **id** in the terminal.
E.g. output: uid=1000(linux) gid=1000(linux) groups=1000(linux), ...

Change the NB_UID and NB_GID with the user's ids and run the container with:

    docker run -it --privileged=true --user root -e NB_USER="$USER" -e NB_UID="$UID" -e NB_GID="$UID" -p 8888:8888 -v "$PWD":/home/"$USER" --name=jupyter gtcap_jupyter

**Note** that JupyterLab can be accessed by adding /lab at the url, instead of /tree (e.g. localhost/lab).

To run the Jupyter server with a predefined token, add at the end of the command:

    start-notebook.sh --NotebookApp.token='abcdefghijk1234567890'

To run with enabled JupyterLab by default add -e JUPYTER_ENABLE_LAB=yes flag e.g.:

    docker run -it --privileged=true --user root -e NB_USER="$USER" -e NB_UID="$UID" -e NB_GID="$UID" -e JUPYTER_ENABLE_LAB=yes -p 8888:8888 -v "$PWD":/home/"$USER" --name=jupyter gtcap_jupyter

For more options visit https://jupyter-docker-stacks.readthedocs.io/en/latest/


To access jupyter server, open in the web browser the link with the token that is provided in the terminal (e.g. http://localhost/tree?token=abcdefghijk1234567890).


Example commands:

    docker run -d -it --privileged=true --user root -e NB_USER="$USER" -e NB_UID="1000" -e NB_GID="1000" -p 80:8888 -v "$PWD":/home/"$USER" --name=jupyter gtcap_jupyter start-notebook.sh --NotebookApp.token='abcdefghijk1234567890'


**Usage Instructions**

All Jupyter Notebooks files have the extension '.ipynb' and are identifiable by the notebook icon next to their name.
To create a new notebook in JupyterLab, go to File -> New and select 'New Notebook'.
Notebooks currently running will have a green dot, while non-running ones will not.
To run a cell with a script, click on the run icon or press Shift+Enter

More information can be found at: https://jupyter.org/documentation

Jupyter Notebook CheatSheet: https://www.edureka.co/blog/wp-content/uploads/2018/10/Jupyter_Notebook_CheatSheet_Edureka.pdf