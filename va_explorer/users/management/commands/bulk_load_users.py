from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from email.utils import parseaddr
import argparse

from va_explorer.users.utils import create_users_from_file


User = get_user_model()

class Command(BaseCommand):

    help = "Create user accounts, assigning a temporary password, given a csv file that has at a minimum email, user group, and location restriction information\
     but can also add any permission information that apears in the user creation form. Run ./manage.py get_user_template to see all such options."

    def add_arguments(self, parser):
        parser.add_argument('user_list_file', type=argparse.FileType('r'))

    def handle(self, *args, **options):
        user_file = options['user_list_file']
        create_users_from_file(user_file)
        self.stdout.write(self.style.SUCCESS('Done!'))



    
    