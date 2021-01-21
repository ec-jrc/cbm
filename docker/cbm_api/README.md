# Creating a docker container for flask micro-framework


Go to cbm folder

    cd cbm

Run the container

    docker run -it -d --name api -v "$PWD":/app -p 80:5000 cbm_api


Folow in real time the logs with

    docker logs -f api

To build the docker image from source run:

    docker build --tag cbm_api .

