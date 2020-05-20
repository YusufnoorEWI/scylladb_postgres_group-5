# scylladb_postgres_group-5

## Running a microservice
First make sure your desired database process is running, so for example look at the install and run ScyllaDB docker image.

Now there are multiple options:

1. Run the flask app directly by running either `python -m <path/to/service>` (without appending .py) or by first running `export FLASK_APP=<path/to/service.py>` and then simply running `flask run` I can recommend this for developing your service as it is quickest to start.

2. Run your app using gunicorn, which significantly increases the performance. To do this first cd into the directory of your microservice, make sure you have installed gunicorn with pip and run the following command: `gunicorn service:app` note that gunicorn runs on port 8000 by default which is different from flask which runs on port 5000.

3. Run your app using docker, see the 'build and run a microservice using docker section' before making a pull request, make sure your app functions accordingly using docker.

## Build and run a microservice using docker
To run a service using docker, a Dockerfile is required like the one in stock_service. Make sure this is the case.

To make life easier for you guys I have defined all the steps of starting services and databases in one single docker-compose.yml file. Now the only thing you should have to do is run `docker-compose up`. This however requires you to install docker-compose.
## Install and run ScyllaDB docker image:
`docker run --name some-scylla -p 9042:9042 -d scylladb/scylla`

## Possible bugs and fixes:
Some machines overprovision scylla inside a docker container. If your scylladb docker container is not working try appending the following: `--smp 2` this will instruct scylladb inside the container to consume less resources. The entire command now looks like this:
`docker run --name some-scylla -p 9042:9042 -d scylladb/scylla --smp 2`

Docker containers communicate to each other using docker networks. By default your dockerized microservice will not be able to communicate with the dockerized database. At some point in time we will have to think about a network between services and databases, but for now the `--network host` flag will suffice.
More on this here: https://docs.docker.com/network/network-tutorial-standalone/
