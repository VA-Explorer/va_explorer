from celery.schedules import crontab

from config.celery_app import app
from config.settings.base import env
from va_explorer.va_data_management.management.commands.import_from_kobo import (
    BATCH_SIZE,
)
from va_explorer.va_data_management.utils import coding, kobo, odk
from va_explorer.va_data_management.utils.loading import load_records_from_dataframe


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    # Import from Kobo daily at 00:00
    sender.add_periodic_task(
        crontab(hour=0, minute=0), import_from_kobo.s(), name="Import from Kobo daily"
    )

    # Run Coding Algorithms daily at 00:30
    sender.add_periodic_task(
        crontab(hour=0, minute=30),
        run_coding_algorithms.s(),
        name="Run Coding Algorithms daily",
    )


# Result of tasks need to be json serializable so return dicts.
@app.task()
def run_coding_algorithms():
    results = coding.run_coding_algorithms()
    return {
        "num_coded": len(results["causes"]),
        "num_total": len(results["verbal_autopsies"]),
        "num_issues": len(results["issues"]),
    }


@app.task()
def import_from_odk():
    options = {
        "email": env("ODK_EMAIL"),
        "password": env("ODK_PASSWORD"),
        "project_id": env("ODK_PROJECT_ID"),
        "form_id": env("ODK_FORM_ID"),
    }
    data = odk.download_responses(
        options["email"],
        options["password"],
        project_id=options["project_id"],
        form_id=options["form_id"],
    )
    results = load_records_from_dataframe(data)
    return {
        "num_created": len(results["created"]),
        "num_ignored": len(results["ignored"]),
        "num_outdated": len(results["outdated"]),
    }


@app.task()
def import_from_kobo():
    options = {
        "token": env("KOBO_API_TOKEN"),
        "asset_id": env("KOBO_ASSET_ID"),
    }
    data, next_page = kobo.download_responses(
        options["token"], options["asset_id"], BATCH_SIZE, None
    )
    results = load_records_from_dataframe(data)

    num_created = len(results["created"])
    num_ignored = len(results["ignored"])
    num_outdated = len(results["outdated"])
    num_corrected = len(results["corrected"])
    num_invalid = len(results["removed"])

    # Process all available pages of kobo data since it is provided via pagination
    while next_page is not None:
        data, next_page = kobo.download_responses(
            options["token"], options["asset_id"], BATCH_SIZE, next_page
        )
        results = load_records_from_dataframe(data)
        num_created = num_created + len(results["created"])
        num_ignored = num_ignored + len(results["ignored"])
        num_outdated = num_outdated + len(results["outdated"])
        num_corrected = num_corrected + len(results["corrected"])
        num_invalid = num_invalid + len(results["removed"])

    return {
        "num_ignored": num_ignored,
        "num_outdated": num_outdated,
        "num_created": num_created,
        "num_corrected": num_corrected,
        "num_removed": num_invalid,
    }
