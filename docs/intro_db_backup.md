# Backing up the database


## Overview

This page explains how to back up database tables. This may be needed as a precaution to avoid loss of data, or to transfer the data to another system.

The following tables are important in any backup, as they determine the values of the foreign keys in the extracted signature tables:

* The **dias_catalogue** database table is required to relate the metadata for the scenes that cover the ROI and which have 'extracted' processing status. This means the _id_ column, which is a sequential number generated when records are ingested, is used as the foreign key _obsid_ in the **roiYYYY_CARD_signatures** database table. This foreign key is needed to cross-reference, for instance, the _reference_ and _obstime_ column values for each record.
* The **parcel_set** database table is required to get the parcel _ogc\_fid_ which is the foreign key _pid_ in the **roiYYYY_CARD_signatures** database table, which is required, for instance, to retrieve the geometry of the parcel and crop type attributes. 
* The **roiYYYY_CARD_signatures** database tables, which contain the extracted values for each combination of _pid_ and _obsid_ for each of the bands of the image sets for the respective CARD sets.

Thus, in order not to loose the explicit relation defined by the foreign keys, a backup must, as a minimum, includes these tables. 


## Use pg_dump

The database is assumed to run within a docker container, for instance, the one derived from the _mdillon/postgis:latest_ image.

Check whether the container is running:


```
docker ps -a
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                     NAMES
7f700d1c67a2        mdillon/postgis     "docker-entrypoint.s…"   20 hours ago        Up 20 hours         0.0.0.0:5433->5432/tcp    pg_spat
```

The default client tool to make database backups for PostgreSQL/Postgis database instances is [_pg\_dump_](https://www.postgresql.org/docs/10/app-pgdump.html). Client tools can be directly installed on the VM that runs the docker container. However, there may be version differences between the _pg\_dump_ version of the docker host and the database running inside the docker container.

For instance, trying to back up the table **dias_catalogue** may cause the following message:

```
pg_dump -h localhost -d postgres -U postgres -p 5433 -t dias_catalogue > dias_catalogue.sql
pg_dump: server version: 11.2 (Debian 11.2-1.pgdg90+1); pg_dump version: 10.6 (Ubuntu 10.6-0ubuntu0.18.04.1)
pg_dump: aborting because of server version mismatch
```

This can be resolved by making sure the client tool is upgraded to 11.2, or, running _pg\_dump_ inside the docker container. The latter is preferred, as it ensures that client tools and database server versions are always aligned.

The sequence is as follows

```
docker exec -it pg_spat bash
root@7f700d1c67a2:/# pg_dump -d postgres -U postgres -t dias_catalogue > /tmp/dias_catalogue.sql
root@7f700d1c67a2:/# exit
docker cp pg_spat:/tmp/dias_catalogue.sql .
```

The first command starts a _bash_ shell inside the container. This causes the command prompt to change to the root user inside the container (root@7f700d1c67a2). 
_pg\_dump_ can now be used with the database that runs inside the container, e.g. to dump the table **dias_catalogue** to the file _/tmp/dias\_catalogue.sql_ inside the container.
After this has finished, exit the container internal _bash_ shell (command prompt turns to the one of the docker host). 
The last command copies the data table dump file from the docker container directory _/tmp_ to the current directory (.)

This file can now be further handled (e.g. compressed) and transferred.
