# Build Jupyter docker image for CbM from source

To build cbm_jupyter docker image from source see the [Jupyter for cbm readme file](https://github.com/ec-jrc/cbm/tree/main/docker/cbm_jupyter#readme)

1. Download the cbm repository:
```sh
git clone https://github.com/ec-jrc/cbm.git
```
In the folder "cbm/docker/jupyter/" there is a "Dockerfile" to create a Jupyter docker image.

2. Navigate to the folder with the docker image file:
```sh
cd cbm/docker/cbm_jupyter
```
3. Build the docker image
```sh
docker build -t gtcap/cbm_jupyter .
```

4.a. Run the Jupyter server  - with no shared folder "bindmount", the files within the container will be deleted if the container is removed:
```sh
docker run -p 8888:8888 gtcap/cbm_jupyter
```
4.b. Or run the Jupyter server  - with a shared folder "bindmount", the files will not be deleted if the container is removed:
- Navigate to the folder you want to bindmount to the container, e.g. the home directory:
```sh
cd ~/
```
Then run the Jupyter server with:
```sh
- docker run -it --privileged=true --user root -e NB_USER="$USER" -e NB_UID="$UID" -e NB_GID="$UID" -p 8888:8888 -v "$PWD":/home/"$USER" --name=jupyter4cbm gtcap/cbm_jupyter
```

The token to access the jupyter server will be in the command line output:
```sh
[I 08:51:48.705 NotebookApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
[C 08:51:48.708 NotebookApp]

   To access the notebook, open this file in a browser:
       file:///home/jovyan/.local/share/jupyter/runtime/nbserver-8-open.html
   Or copy and paste one of these URLs:
       http://abcd12345678:8888/?token=abcd12345678
    or http://127.0.0.1:8888/?token=abcd12345678
```

You will be able to access the Jupyter server on port 8888 (or any other port) on VM's public ip e.g.: **0.0.0.0:8888**
Copy the token from the command line and add it to the web interface.
