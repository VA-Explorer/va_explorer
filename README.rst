VA Explorer
===========

Django Demo for VA Explorer

.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
     :target: https://github.com/ambv/black
     :alt: Black code style


:License: MIT

The VA Application prototype is a Django application that uses a PostgreSQL database and the Cookiecutter Django starter app. Cookiecutter provides support for Celery, Docker, amongst other dependencies.

Caveats
-------
The instructions outlined in this README were tested on macOS.

Prerequisites
-------------
* pip: the application was developed on a machine with pip version 20.1.1
* postgresql: the application was developed on a machine using psql version 12.3


Settings
--------

The Cookiecutter Django starter app has extensive documentation on settings_.

.. _settings: http://cookiecutter-django.readthedocs.io/en/latest/settings.html

Getting Up And Running
----------------------

Local Environment
^^^^^^^^^^^^^^^^^
* Create a virtual env::

    $ python3 -m venv venv

* Activate the virutal env::

    $ source venv/bin/activate

* Install development requirements**::

    $ pip install -r requirements/local.txt

* The .env file at the project route contains a sample postgresql setup for this demo app. You may override these settings (e.g., the database user, etc.) if you so choose in the .env file.
    * To use the settings in the .env file, first create the user va_admin using the psql command line::

        $  psql -U postgres --password
        $  postgres=# CREATE USER va_admin WITH PASSWORD 'rGgEuXv9A8BxKbp9EKPULaFM';
        $  postgres=# ALTER USER va_admin CREATEDB;


    * Next, create the va_explorer database::

        $ createdb va_explorer -U va_admin --password rGgEuXv9A8BxKbp9EKPULaFM

* Run the database migrations::

        $ python3 manage.py migrate

* Create the **superuser account**::

    $ python3 manage.py seedadmin

* Run the application::

        $ python3 manage.py runserver 0.0.0.0:8000

* Log into the local application with the superuser you just seeded:
    * Email: admin@example.com
    * Password: Password1

** Note on pyscopg2: If the installation of psycopg2 fails, consult this post_ on stackoverflow.

.. _post: https://stackoverflow.com/questions/39767810/cant-install-psycopg2-package-through-pip-install-is-this-because-of-sierra

Type checks
^^^^^^^^^^^

Running type checks with mypy:

::

  $ mypy va_explorer

Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

Running tests with py.test
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ pytest

Live reloading and Sass CSS compilation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Moved to `Live reloading and SASS compilation`_.

.. _`Live reloading and SASS compilation`: http://cookiecutter-django.readthedocs.io/en/latest/live-reloading-and-sass-compilation.html



Celery
^^^^^^

This app comes with Celery.

To run a celery worker:

.. code-block:: bash

    cd va_explorer
    celery -A config.celery_app worker -l info

Please note: For Celery's import magic to work, it is important *where* the celery commands are run. If you are in the same folder with *manage.py*, you should be right.




Email Server
^^^^^^^^^^^^

In development, it is often nice to be able to see emails that are being sent from your application. For that reason local SMTP server `MailHog`_ with a web interface is available as docker container.

Container mailhog will start automatically when you will run all docker containers.
Please check `cookiecutter-django Docker documentation`_ for more details how to start all containers.

With MailHog running, to view messages that are sent by your application, open your browser and go to ``http://127.0.0.1:8025``

.. _mailhog: https://github.com/mailhog/MailHog


Docker
^^^^^^

See detailed `cookiecutter-django Docker documentation`_.

.. _`cookiecutter-django Docker documentation`: http://cookiecutter-django.readthedocs.io/en/latest/deployment-with-docker.html
