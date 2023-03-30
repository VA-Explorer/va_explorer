# Development

Thank you for your interest in helping to make VA Explorer even better! These
guides should help you get setup for local development. Afterwards, you should
be ready to tackle [Issues](https://github.com/VA-Explorer/va_explorer/issues). We recommend the ones tagged
`good first issue` as a starting point.

As a pre-requisite you should have the following already on your system:

- Python 3 + pip
- Postgres
- Docker

## Setting Up & Building

Like the process described in the VA Explorer `README.md`:

1. Retrieve the application source code

```shell
git clone https://github.com/VA-Explorer/va_explorer.git
```

2. Change into the new directory

```shell
cd va_explorer
```pref

3. Create a virtual env

```shell
python -m venv venv
```

4. Activate the virtual env:

```shell
source venv/bin/activate
```

5. Install application requirements

```shell
pip install -r requirements/base.txt
```

6. Create the va_explorer database using your postgres user made during postgres
download. It may be `postgres` for example.

```shell
createdb va_explorer -U <name of Postgres user> --password`
```

7. Create a .env file at the project root with the following key/value pairs:

```ini
DATABASE_URL=psql://<YOUR POSTGRESUSER>:<POSTGRESUSER PASSWORD>@localhost/va_explorer
CELERY_BROKER_URL=redis://localhost:6379/0
```

8. Run the database migrations

```shell
./manage.py makemigrations
./manage.py migrate
```

This will prepare your local development environment to run VA Explorer locally
via the `runserver_plus` command (see [Development Commands](#development-commands)).
Next you will want to seed VA Explorer with some example data so you can login
and see its features in action. To do that run:

1. Create user roles & permissions source code

```shell
./manage.py initialize_groups
```

2. Create an admin user for yourself. The values can be fake, you just need to
remember them to login

```shell
./manage.py seed_admin_user <EMAIL_ADDRESS> --password=<PASSWORD>
```

3. Create some demo accounts if you’d like to try out the other roles too

```shell
./manage.py seed_demo_users
```

4. If you have locations for geographic access restrictions on hand, load those via

```shell
./manage.py load_locations <NAME OF CSV>
```

5. If you have {term}`VA`s on hand, you should also load them now

```shell
./manage.py load_va_csv <NAME OF CSV>
```

6. Finally, if you’d like to try out the coding algorithm assignment
functionality, build just those docker services and run them manually via:

```shell
docker-compose up -d --build pycrossva interva5
./manage.py run_coding_algorithms
```

You can also run the rest of the docker build, the part of VA Explorer that is
deployed for users, by running `docker-compose up -d --build` to build the rest
of the containers.

## Testing & Running Locally

After setup, you’re ready to run VA Explorer locally! If you’ve run:

```shell
./manage.py runserver_plus 0.0.0.0:8000
```

then you should be able to navigate to `localhost:8000` in the browser of your
choice and be presented with the sign in screen. Signing in here with the admin
user you seeded earlier should open up access to the rest of the features, as
described in [Features](usage/features).

```{note}
Data seeded for local instances of VA Explorer lives in your local installation
of PostgreSQL, so you should be able to examine the data by running `psql -U postgres`
and connecting to the `va_explorer` database.
```

If you’re trying out the built docker version of VA Explorer locally, you should
be able to navigate to the docker deployment of VA Explorer by going to
`localhost:5000` in your browser after building. Unlike your local instance, data
seeded for this will only exist if you `docker exec` into the `django` docker
service. That data lives in the `postgres` docker service, separate from your
local installation of PostgreSQL.

Finally, developers should be able to test easily and often with the built-in
testing utility. To run the test suite use `pytest`. When running these, you may
be required to install Firefox or geckodriver to do browser-based tests. See the
Selenium Client Driver Documentation for more info if needed.

## Running Integrations Locally

If you would like to test or contribute to the functionality of VA Explorer
integrations and would like to use the real instances of {term}`ODK` Central
and {term}`DHIS2` locally, please see to the documentation from those two
services. They are the best reference.

- [ODK Central](https://docs.getodk.org/central-intro/)
- [DHIS2](https://developers.dhis2.org/docs)
  - [via Docker](https://hub.docker.com/r/dhis2/core)

## Development Commands

As mentioned in [Management Commands](training/admin_guides.md#management-commands),
VA Explorer provides additional functionality beyond its UI-based features. This
holds especially true for development which has relevant actions detailed here:

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.50\linewidth-2\tabcolsep}|
.. flat-table:: List of all configuration options when interfacing with the pyCrossVA service, plus default values and descriptions for each
  :widths: 3 3 5
  :header-rows: 2

  * - :rspan:`1` Command Name
    - Parameter Names
    - :rspan:`1` Description

  * - ``(*)`` = Required

  * - ``makemigrations``
    - See Ext. Docs
    - A built-in django admin command used to generate new migration files based
      on changes detected to VA Explorer models.

  * - ``migrate``
    - See Ext. Docs
    - A built-in django admin command used to sync the VA Explorer database
      state with the current set of models and migrations in the app code by
      applying migrations files.

  * - ``shell_plus``
    - None
    - A django-extensions command that provides a python shell session preloaded
      with VA Explorer database models and other user-defined classes. Useful
      for running python commands that require VA Explorer components.

  * - ``collectstatic``
    - See Ext. Docs
    - A built-in django admin command that collects all static files into
      ``STATIC_ROOT``. Useful for refreshing the application during development
      after adding new static files.

  * - ``runserver_plus``
    - ``ip:port`` or See Ext. Docs
    - A django-extensions command that runs a development server to serve VA
      Explorer locally. Has extras that support errors and debugging. Optionally
      specify an ``ip:port`` format location to run the server on a specific IP
      address and port number. Defaults to ``127.0.0.1:8000``

  * - ``validate_templates``
    - See Ext. Docs
    - A django-extensions command used to catch any invalid Django template
      syntax within your app. Used by VA Explorer in its testing.

  * - ``initialize_groups``
    - None
    - Used to manually run or update user roles and their associated permissions.

  * - :rspan:`1` ``seed_admin_user``
    - ``--email`` ``(*)``
    - :rspan:`1` Creates an admin user with a specific email address and
      password. Optionally accepts a password via `password` param, but will
      create a randomly-generated password and print to the console by default.

  * - ``--password``

  * - ``seed_demo_users``
    - None
    - Creates demo accounts for Data manager, Data viewer, and Field Worker with
      ``Password1``. Used for the local environment only for demonstration and
      testing purposes.

  * - ``fake_current_va_dates``
    - None
    - Updates dates on all VAs to make them look more current. Used for the
      local environment only for demonstration and testing purposes.

  * - ``randomize_va_dates``
    - None
    - Initializes demo VAs with dates. Used for the local environment only for
      demonstration and testing purposes.

````

Additionally, the full and complete list of management commands (only some of
the most popular are described here or in [Management Commands](training/admin_guides.md#management-commands)) is available
by running `manage.py help`.
