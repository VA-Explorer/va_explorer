import argparse

from django.core.management.base import BaseCommand

from va_explorer.users.utils.field_worker_linking import link_fieldworkers_to_vas


class Command(BaseCommand):

    help = "Create user accounts, assigning a temporary password, given a csv file that has at a minimum email, user group, and location restriction information\
     but can also add any permission information that apears in the user creation form. Run ./manage.py get_user_template to see all such options."

    def add_arguments(self, parser):
        parser.add_argument('--emails', help="List of field worker emails to check for during linking. \
            Provide as one, comma-separated string. Ex. abc@email.com,def@email.com", type=argparse.FileType('r'))
        parser.add_argument('--match_threshold', type=float, nargs='?', default=.80)
        parser.add_argument('--debug', type=bool, nargs='?', default=False)


    def handle(self, *args, **options):
        emails = options.get('emails', None)
        if emails:
            emails = [e.strip() for e in emails.split(',')]
        match_threshold = options.get("match_threshold", .80)
        debug = options.get('debug', False)
        link_fieldworkers_to_vas(emails=emails, match_threshold=match_threshold, debug=debug)

