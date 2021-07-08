from config.settings.base import LOGGING, LOG_DIR
import os
from django.core.management import BaseCommand

class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    help = "Initialize log directories for event loggig and debugging"

    def handle(self, *args, **options):
    	if not os.path.isdir(LOG_DIR):
    		try:
    			os.mkdir(LOG_DIR)
    			print(f"Made log directory at {LOG_DIR}")
    		except:
    			raise FileNotFoundError(f"Couldnt create log directory {LOG_DIR}")
    	handlers = LOGGING["handlers"]
    	for handler_name, cfg in handlers.items():
    		logfile = cfg.get("filename", None)
    		if logfile:
    			if not os.path.isfile(logfile):
    				try:
    					with open(logfile, "w") as out:
    						pass
    					print(f"Made new logfile {logfile}")
    				except:
    					raise FileNotFoundError(f"Couldnt create log file {logfile}")
