
FROM python:3.12-slim-bookworm AS python

FROM python AS python-build-stage

RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg dependencies
  libpq-dev

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
# Create Python Dependency and Sub-Dependency Wheels
RUN pip wheel --wheel-dir /usr/src/app/wheels \
  -r ./requirements/production.txt

FROM python AS python-run-stage

ARG APP_HOME=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR ${APP_HOME}

RUN addgroup --system django \
  && adduser --system --ingroup django django

# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  libpq-dev \
  gettext \
  wait-for-it \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# All absolute dir copies ignore workdir instruction. All relative dir copies
# are wrt to the workdir instruction. copy python dependency wheels from python-build-stage
COPY --from=python-build-stage /usr/src/app/wheels /wheels/

# use wheels to install python dependencies
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
  && rm -rf /wheels/


# Copy all commands.
COPY --chown=django:django ./compose/django/entrypoint /entrypoint
COPY --chown=django:django ./compose/django/start /start
COPY --chown=django:django ./compose/django/celery/worker/start /start-celeryworker
COPY --chown=django:django ./compose/django/celery/beat/start /start-celerybeat
COPY --chown=django:django ./compose/django/celery/flower/start /start-celeryflower

RUN chmod +x /entrypoint /start /start-celeryworker /start-celerybeat /start-celeryflower
RUN sed -i 's/\r$//g' /entrypoint /start /start-celeryworker /start-celerybeat /start-celeryflower

# copy application code to WORKDIR
COPY --chown=django:django manage.py /app/manage.py
COPY --chown=django:django locale /app/locale
COPY --chown=django:django .env /app/.env
COPY --chown=django:django config /app/config
COPY --chown=django:django va_explorer /app/va_explorer

RUN python /app/manage.py collectstatic --noinput --settings=config.settings.production

USER django

ENTRYPOINT ["/entrypoint"]
