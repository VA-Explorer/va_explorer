# Configuration & Deployment

VA Explorer configuration is primarily set by `docker-compose.yml` with sensible
defaults. Admins or {term}`IT` Staff with access to the server hosting a VA Explorer
instance can change this configuration via the `.env` file. To begin using this
file (if you haven’t already during Installation & Setup’s Step 4) you can use
`mv .env.template .env` and `vim .env` to open a `.env` file for editing. To
give an idea for how the VA Explorer could be changed each of the options is
documented below.

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.30\linewidth-2\tabcolsep}|p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.45\linewidth-2\tabcolsep}|
.. flat-table:: List of all configuration options for the base VA Explorer app along with default values and descriptions for each, plus external references where appropriate
  :widths: 3 3 5
  :header-rows: 1
  :stub-columns: 1

  * - Variable Name
    - Default Value
    - Description

  * - ``DJANGO_DEBUG``
    - Not Set
    - ``True`` or ``False``. Will configure VA Explorer to report additional
      info in logs, error pages, console messages, and via a debug toolbar if
      ``True``. Not set by default to allow settings.local or
      settings.production to handle value.

  * - ``EMAIL_URL``
    - ``consolemail://``
    - A `Django Environ <https://django-environ.readthedocs.io/en/latest/types.html#environ-env-email-url>`_
      ``email_url`` which supports various email related URL schemas. Used to
      allow VA Explorer to connect to an email server and send email on your
      behalf. Setup to print to the console (docker logs) by default.
      **Recommended to customize.**

  * - ``DJANGO_DEFAULT
      _FROM_EMAIL``
    - ``VA Explorer <noreply@vaexplorer.org>``
    - The email address used in the sender field when VA Explorer sends
      automated emails. Format options include ``Name <email>`` or ``email``.
      Default is app value here instead of
      `Django default <https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-DEFAULT_FROM_EMAIL>`_.
      **Recommended to customize.**

  * - ``DJANGO_SECRET_KEY``
    - ``dcc02e52ccbb649b9feb
      e9182abfa5e03c49be6c``
    - Hash `used by Django to cryptographically sign <https://docs.djangoproject.com/en/4.1/topics/signing/>`_
      things like sessions and account recovery email urls. Defaults to the
      given hard-coded random hash. **Recommended to customize.**

  * - ``DJANGO_ALLOWED_HOSTS``
    - ``localhost``
    - A list of comma separated ``ip:port`` or ``unix:path`` formatted strings
      representing the host's or domain names that VA Explorer can serve. A
      security measure to prevent Host header attacks. Defaults to local
      computer browser only. **Recommended to customize**.

  * - ``CELERY_BROKER_URL``
    - ``redis://redis:6379/0``
    - A `Celery supported backend <https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/index.html>`_
      URL schema. Allows VA Explorer to support reading results from
      long-running tasks such as batch cause-of-death assignment. Points to
      built-in redis service by default.

  * - ``REDIS_URL``
    - ``redis://redis:6379/0``
    - ``ip`` ``port`` or ``unix:path`` format location for
      `Django caching solution <https://docs.djangoproject.com/en/4.1/topics/cache/>`_.
      Default allows VA Explorer to take advantage of same redis
      available as celery backend so is often the same value.

  * - ``CELERY_FLOWER_USER``
    - Not Set
    - Value indicating the username needed by the basic auth prompt that shows when
      attempting to access the celery flower interface. Not set by default.

  * - ``CELERY_FLOWER_PASSWORD``
    - Not Set
    - Value indicating the password needed by the basic auth prompt that shows when
      attempting to access the celery flower interface. Not set by default.
````

% Comment: We break the table in half here because the pdf rendering was flying off the page

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.30\linewidth-2\tabcolsep}|p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.45\linewidth-2\tabcolsep}|
.. flat-table::
  :widths: 3 3 5
  :header-rows: 0
  :stub-columns: 1

  * - ``POSTGRES_HOST``
    - ``vapostgres``
    - Value indicating the postgres host location. Formatted as a
      `PostgreSQL host <https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNECT-HOST>`_
      parameter. Default value points to built-in postgres docker container.

  * - ``POSTGRES_PORT``
    - ``5432``
    - Value indicating the port postgres runs on at the host location. Formatted
      as a `PostgreSQL port <https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNECT-PORT>`_
      parameter. Default points to postgres port of built-in service.

  * - ``POSTGRES_DB``
    - ``va_explorer``
    - Value indicating the name of the database used by VA Explorer. Formatted
      as a `PostgreSQL dbname <https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNECT-DBNAME>`_
      parameter. Default is name of app.

  * - ``POSTGRES_USER``
    - ``postgres``
    - Value indicating the name of the user accessing postgres. Formatted as a
      `PostgreSQL user <https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNECT-USER>`_
      parameter. Defaults to standard user.

  * - ``POSTGRES_PASSWORD``
    - ``postgres``
    - Value indicating the password to use for the user accessing postgres.
      Formatted as a `PostgreSQL password <https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNECT-PASSWORD>`_
      parameter. Defaults to standard pass of built-in service. **Recommended to
      customize**.

  * - ``QUESTIONS_TO_
      AUTODETECT_DUPLICATES``
    - ``"Id10017,Id10018,Id10019,
      Id10020,Id10021,Id10022,Id10023"``
    - A list of comma separated fields corresponding to questions on a VA
      `(See standard) <https://www.who.int/standards/classifications/other-classifications/verbal-autopsy-standards-ascertaining-and-attributing-causes-of-death-tool>`_.
      Allows for customization of which fields VA Explorer considers when
      attempting to detect duplicate VAs. Defaults to fields having to do with
      name, sex, date of birth, and date of death.
````

Config values are read from `.env` first, then `docker-compose.yml` if unset,
and finally from framework settings in `config/settings/production.py` during
end-user docker builds when config hasn't been set elsewhere.

```{note}
If you update any of these configuration variables, please also run
`docker-compose up -d` once more to push your `.env` file updates to the various
containers.
```

For further configuration information, particularly for integrating with
external services such as {term}`ODK` and {term}`DHIS2`, please see [Integrations](../integrations.md).
