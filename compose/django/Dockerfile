
FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Translations dependencies
  && apt-get install -y gettext \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN addgroup --system django && adduser --system --ingroup django django

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
RUN pip install --no-cache-dir -r /requirements/production.txt

# Copy all commands.
COPY ./compose/django/entrypoint /entrypoint
COPY ./compose/django/start /start
COPY ./compose/django/celery/worker/start /start-celeryworker
COPY ./compose/django/celery/beat/start /start-celerybeat
COPY ./compose/django/celery/flower/start /start-celeryflower

RUN chmod +x /entrypoint /start /start-celeryworker /start-celerybeat /start-celeryflower
RUN chown django /entrypoint /start /start-celeryworker /start-celerybeat /start-celeryflower
RUN sed -i 's/\r$//g' /entrypoint /start /start-celeryworker /start-celerybeat /start-celeryflower

RUN mkdir /app && chown django /app

USER django

COPY --chown=django:django .env /app/.env
COPY --chown=django:django manage.py /app/manage.py
COPY --chown=django:django va_explorer /app/va_explorer
COPY --chown=django:django config /app/config
COPY --chown=django:django locale /app/locale

RUN python /app/manage.py collectstatic --settings=config.settings.production

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
