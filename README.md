# scylladb_postgres_group-5


## Install and run ScyllaDB docker image:
`docker run --name some-scylla -p 9042:9042 -d scylladb/scylla`

## Possible bugs and fixes:
Some machines overprovision scylla inside a docker container. If your scylladb docker container is not working try appending the following: `--smp 2` this will instruct scylladb inside the container to consume less resources. The entire command now looks like this:
`docker run --name some-scylla -p 9042:9042 -d scylladb/scylla --smp 2`
