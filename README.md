## VA Explorer Web Application Prototype

VA Explorer is a prototype web application, built to both demonstrate verbal autopsy data management and
analysis capabilities and act as a foundation for exploring new concepts. This prototype represents a
work-in-progress, and is expected to mature in response to feedback from users and subject matter experts.
VA Explorer currently supports the following functionality at various degrees of maturity:

* User account management, including:
  *  Creation/disabling of user accounts by administrators
  *  Password management for individual users
* User access controls, including:
  *  Role-based access with the following roles: administrators, data managers, data viewers,
  and field workers
  *  Assignment to one or more geographic areas for geographical-level scoping of data
* Loading of verbal autopsy questionnaire data
* Assignment of cause of death using InterVA5 algorithm (Note: relies on external pyCrossVA and
InterVA5 services)
* Exploration of cause of death data via a dynamic, visualization-based dashboard that includes:
  *  A dynamic heatmap showing geographical trends, with zoom capabilities to hone in on regions
  of interest
  *  Cause of death plots for chosen regions
  *  Death distributions by age, gender, and place of death for chosen regions
  *  Trends over time for chosen regions

### Background

Verbal autopsies (VAs) are structured interviews for determining the most likely cause of death based on
information from caregivers or family members about the signs and symptoms the deceased experienced before
they died. The current VA IT landscape consists of tools and systems that together enable the various
steps of the VA process, from generation and revision of a VA interview questionnaire to the eventual
use of the resulting cause of death data by localities. By directly integrating with existing
functionality, drawing inspiration from others, and combining new features into a cohesive whole,
VA Explorer aims to enable the integration of verbal autopsy into civil registration and vital
statistics systems at scale.

### Installation and Setup for Development or Testing

VA Explorer is a Django web application that uses the PostgreSQL database for data storage.

#### Prerequisites

To work with the application, you will need to install some prerequisites:

* [Python 3](https://www.python.org/downloads/)
* [pip](https://pypi.org/project/pip/)
* [Postgres](http://www.postgresql.org/)

Once the prerequisites are available, VA Explorer can be installed and demonstration data can be loaded.

#### Setup

* Retrieve the application source code

    `git clone https://github.com/<REPO_NAME>`

* Change into the new directory

    `cd va_explorer`

* Create a virtual env

    `python -m venv venv`

* Activate the virtual env:

    `source venv/bin/activate`

* Install application requirements

    `pip install -r requirements/local.txt`

* Create the va_explorer database

    `createdb va_explorer -U <name of Postgres user> --password`

* Create a .env file at the project root with the following key/value pairs:

    *  `DATABASE_URL=psql://<YOUR POSTGRESUSER>:<POSTGRESUSER PASSWORD>@localhost/va_explorer`
    *  `CELERY_BROKER_URL=redis://localhost:6379/0`
    *  `USE_DOCKER="no"`


* Run the database migrations
    * `python manage.py makemigrations`
    * `python manage.py migrate`

#### Tasks

* Manage user accounts

  * Create user roles

    `python manage.py initialize_groups`

  * Create an administrator user for the local environment (note that for the production environment instead of providing the password on the command line a system-assigned, randomly-generated password will be printed to the console)

    `python manage.py seed_admin_user <EMAIL_ADDRESS> --password <PASSWORD>`

  * Create demonstration accounts for data manager, data viewer, and field worker. This task
  only works in the local environment and is for demonstration purposes, only.

    `python manage.py seed_demo_users`

* Load location data

  `python manage.py load_locations <NAME OF CSV>`

* Load verbal autopsy questionnaire data

  `python manage.py load_va_csv <NAME OF CSV>`

* Run the InterVA5 cause of death coding algorithm

  `python manage.py run_coding_algorithms`

The InterVA5 cause of death coding algorithm requires two microservices: pyCrossVA and InterVA5. For
instructions on setting up and running these microservices, please see:
[pyCrossVA](https://github.com/pkmitre/pyCrossVA/tree/microservice-experiment) and
[InterVA5](https://github.com/pkmitre/InterVA5/tree/microservice-experiment)

* Run the tests

    `pytest`

#### Running the application

* Run the application server

    `python manage.py runserver 0.0.0.0:8000`

    The server will be running at http://0.0.0.0:8000/

### Version History

This project adheres to [Semantic Versioning](http://semver.org/).

Releases are documented in the [CHANGELOG]().

### License

Copyright 2020 The MITRE Corporation

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

```
http://www.apache.org/licenses/LICENSE-2.0
```

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

### Contact Information

For questions or comments about VA Explorer, please send an email to:

```
verbal-autopsy@mitre.org
```
