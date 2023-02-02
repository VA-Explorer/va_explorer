# Configuration & Deployment

VA Explorer configuration is primarily set by `docker-compose.yml` with sensible
defaults. Admins or IT Staff with access to the server hosting a VA Explorer
instance can change this configuration via the `.env` file. To begin using this
file (if you haven’t already during Installation & Setup’s Step 4) you can use
`mv .env.template .env` and `vim .env` to open a `.env` file for editing. To
give an idea for how the VA Explorer could be changed each of the options is
documented below.

```{csv-table}
:header: Variable Name, Default Value, Description
:stub-columns: 1
:escape: \
`DEBUG`,`False`,`True` or ```{code-block}False```. Will configure VA Explorer to report additional info in logs and console messages if `True`. Defaults to `False` for standard info.
`EMAIL_URL`,`consolemail://`,A <a class="inline-external" href="https://django-environ.readthedocs.io/en/latest/types.html#environ-env-email-url">Django Environ</a> `email_url` which supports various email related URL schemas. Used to allow VA Explorer to connect to an email server and send email on your behalf. Setup to print to the console (docker logs) by default. **Recommended to customize.**
`DJANGO_DEFAULT_FROM_EMAIL`,`VA Explorer <noreply@vaexplorer.org>`,The email address used in the sender field when VA Explorer sends automated emails. Format options include `Name <email>` or `email`. Default is app value here instead of <a class="inline-external" href="https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-DEFAULT_FROM_EMAIL">Django default</a>. **Recommended to customize.**
`DJANGO_SECRET_KEY`,`dcc02e52ccbb649b9febe9182abfa5e03c49be6c`,Hash used by Django to cryptographically sign things like account recovery email urls. Defaults to hard-coded random hash. **Recommended to customize.**
`DJANGO_ALLOWED_HOSTS`,`localhost`,A list of comma separated ip:port or unix:path formatted strings representing the hosts or domain names that VA Explorer can serve. A security measure to prevent Host header attacks. Defaults to local computer browser only. Recommended to customize.
`CELERY_BROKER_URL`,`redis://redis:6379/0`,A Celery supported backend URL schema. Allows VA Explorer to support reading results from long-running tasks such as batch cause-of-death assignment. Points to built-in redis service by default.
`REDIS_URL`,`redis://redis:6379/0`,`ip` `port` or `unix:path` format location for Django caching solution. Default allows VA Explorer to take advantage of same redis available as celery backend so is often the same value.
`POSTGRES_HOST`,`vapostgres`,Value indicating the postgres host location. Formatted as a PostgreSQL host parameter. Default value points to built-in postgres docker container. 
`POSTGRES_PORT`,`5432`,Value indicating the port  postgres runs on at the host location. Formatted as a PostgreSQL port parameter. Default points to postgres port of built-in service.
`POSTGRES_DB`,`va_explorer`,Value indicating the name of the database used by VA Explorer. Formatted as a PostgreSQL dbname parameter. Default is name of app.
`POSTGRES_USER`,`postgres`,`Value indicating the name of the user accessing postgres. Formatted as a PostgreSQL user parameter. Defaults to standard user.
`POSTGRES_PASSWORD`,`Pimin73y!we`,Value indicating the password to use for the user accessing postgres. Formatted as a PostgreSQL password parameter. Defaults to hard-coded random value. Recommended to customize.
`QUESTIONS_TO_AUTODETECT_DUPLICATES`,`Id10017\, Id10018\, Id10019\, Id10020\, Id10021\, Id10022\, Id10023`,A list of comma separated fields corresponding to questions on a VA (See standard). Allows for customization of which fields VA Explorer considers when attempting to detect duplicate VAs. Defaults to fields having to do with name\, sex\, date of birth\, and date of death.
```

```{note}
If you update any of these configuration variables, please also run
`docker-compose up -d` once more to push your `.env` file updates to the various
containers.
```

For further configuration information, particularly for integrating with
external services such as ODK and DHIS, please see Integrations (link).
