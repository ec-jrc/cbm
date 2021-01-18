This sub-folder contains scripts that will normally run as automated routines,
e.g. cron tasks or docker swarm stacks (in contrast to interactive notebooks).

It contains configuration files for database access and S3 storage access (the
latter only as template). These configuration files need to be adapted to the
specific DIAS instances.

The docker_compose\*.yml file configure docker swarm stacks that distribute
(extraction) tasks over multiple VMs.


