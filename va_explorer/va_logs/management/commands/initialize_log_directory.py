import os

from django.core.management import BaseCommand

from config.settings.base import LOG_DIR, LOGGING


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "Initialize log directories for event loggig and debugging"

    def handle(self, *args, **options):
        _ = (args, options)  # unused
        if not os.path.isdir(LOG_DIR):
            try:
                os.mkdir(LOG_DIR)
                try:
                    os.chown(LOG_DIR, gid=101, uid=101)
                except Exception as err:
                    print(f"failed to change ownership of {LOG_DIR}: {str(err)}")
                print(f"Made log directory at {LOG_DIR}")

            except Exception as err:
                raise FileNotFoundError(
                    f"Couldn't create log directory {LOG_DIR}: {str(err)}"
                )

        handlers = LOGGING["handlers"]
        for _, cfg in handlers.items():
            logfile = cfg.get("filename", None)
            if logfile and not os.path.isfile(logfile):
                try:
                    open(logfile, "w")  # noqa: SIM115 - just trying to create file
                    print(f"Made new logfile {logfile}")
                except Exception as err:
                    raise FileNotFoundError(
                        f"Couldn't create log file {logfile}: {str(err)}"
                    )
