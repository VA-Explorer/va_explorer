# IT Support

The VA Explorer team anticipates that there may be {term}`IT` staff supporting the use
of VA Explorer and recognizes that {term}`IT` training for VA Explorer is different from
that for day-to-day VA Explorer admins.  The guides in this section outline
estimated level of support for interested {term}`IT` groups within organizations and to
cover guidance this final type of user and their abilities. In some cases, the
VA Explorer administrator may also serve as the {term}`IT` staff.

## Levels of Support Recommended for VA Explorer

This section will describe the levels of support within a country needed to
install and maintain the VA Explorer system. While VA Explorer is pre-configured
to run on deployment, VA Explorer integrates with other systems and having a
system administrator who has the necessary skills to maintain the system over time
is crucial to long term success. {term}`IT` support can do more complex tasks than VA
Explorer admins characterized by overall system installation, deployment, and
maintenance that may occur outside of VA Explorer itself.  The estimate of
level-of-support described below is presented as reference only, and your
jurisdiction may have specific needs that change these requirements.

__Required:__

- Basic understanding of/experience with Docker
- Copy files into/out of Docker containers and exec into/out of containers
- Change configuration settings/environment variables
- Experience with Linux systems and ssh

__Nice To Haves:__

- Basic knowledge of Django (particularly management commands)
- Familiarity with {term}`ODK` {term}`VA` form/ how to set up an {term}`ODK` instance

__Estimated time investment:__

- Initial deployment: approximately 1 day to 1 week, depending on experience
- Maintenance: approximately 1-8 hours a week to debug and troubleshoot

Additionally, those {term}`IT` teams wishing to contribute to the development of VA
Explorer would also benefit from web development experience, particularly with
Django. Development methods are discussed more in [Development](../develop).

## Backing Up VA Explorer

VA Explorer is distributed with utilities to backup data from the built-in
database service. However, the server itself is something left to {term}`IT` Staff/Admins
to backup if desired. Some popular options for this are taking incremental backups
of the server filesystem via snapshot utility Rsnapshot or even simple shell script.

Whichever method is chosen, establishing a regular backup method will help
protect against critical loss of VA Explorer components such as your `.env` file,
https certificates, reverse proxy configurations, and other items from previous
installation and setup.

## Upgrading VA Explorer

Those wanting to upgrade to the latest version of VA Explorer can do so easily
via git, the same way they installed the software. Do another `git pull`,
ensuring that any changes you or your organization have made such as configuring
the `.env` file, are not erased.

If {term}`IT` Admins need to migrate to a newer postgres database, as is occasionally
the case, then that process is a bit more involved:

0. (optional) If existing migration volumes exist from a past upgrade, delete
   those now:

```shell
docker volume rm va_explorer_migration_postgres_data va_explorer_migration_postgres_data_backups
```

1. Make a logical backup of all current data

```shell
docker exec -it va_explorer_vapostgres_1 /usr/bin/pg_dumpall -U postgres > ~/dumpfile
```

2. Make backups of old volumes by cloning data

- Get docker-compose labels

```shell
docker volume inspect va_explorer_production_postgres_data
```

```shell
docker volume create \
    --label com.docker.compose.project="va_explorer" \
    --label com.docker.compose.version="1.26.0" \
    --label com.docker.compose.volume="migration_postgres_data" \
    va_explorer_migration_postgres_data
```

- Clone data

```shell
docker container run --rm -it -v va_explorer_production_postgres_data:/from -v va_explorer_migration_postgres_data:/to alpine ash -c "cd /from ; cp -av . /to"
```

- Repeat for backup volumes

```shell
docker volume inspect va_explorer_production_postgres_data_backups
```

```shell
docker volume create \
    --label com.docker.compose.project="va_explorer" \
    --label com.docker.compose.version="1.26.0" \
    --label com.docker.compose.volume="migration_postgres_data_backups" \
    va_explorer_migration_postgres_data_backups
```

```shell
docker container run --rm -it -v va_explorer_production_postgres_data_backups:/from -v va_explorer_migration_postgres_data_backups:/to alpine ash -c "cd /from ; cp -av . /to"
```

3. Delete old volumes that no longer work with postgres version

```shell
docker volume rm va_explorer_production_postgres_data va_explorer_production_postgres_data_backups
```

4. Build new VA Explorer release & rebuild fresh old volumes (no data)

```shell
docker-compose down && docker-compose build && docker-compose up -d
```

5. Copy over backup dumpfile data to new container

```shell
docker cp ~/dumpfile va_explorer_vapostgres_1:/tmp/dumpfile
```

```shell
docker exec -it va_explorer_vapostgres_1 bash
```

```shell
psql -U postgres
```

```{note}
`DROP DATABASE` may fail as the new container does migrations, just re-try
```

```sql
DROP DATABASE va_explorer;
CREATE DATABASE va_explorer;
```

```shell
psql -U postgres < /tmp/dumpfile
exit
```

6. Run `docker-compose restart`

7. Confirm that all data made it / backup & restore appears successful

8. Use the old volumes `va_explorer_migration_postgres_data` and
`va_explorer_migration_postgres_data_backups` to rollback if needed.

See also any release notes associated with new VA Explorer versions that may
contain version-specific upgrade instructions in the future.
