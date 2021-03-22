from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from email.utils import parseaddr
import argparse
import re

User = get_user_model()

class Command(BaseCommand):

    help = "Create user accounts, assigning a temporary password, given file with a list of user emails (one per line, standard email format with name)"

    def add_arguments(self, parser):
        parser.add_argument('user_list_file', type=argparse.FileType('r'))

    def handle(self, *args, **options):
        users = options['user_list_file'].read().splitlines()
        for user in users:
            name, email = parseaddr(user.strip())
            if not re.match('[^@]+@[^@]+\.[^@]+', email):
                print(f'Invalid email address found: {email}')
                continue
            if len(name.strip()) == 0:
                name = email
            if User.objects.filter(email=email).exists():
                print(f'User account already exists for email {email}')
            else:
                user, created = User.objects.get_or_create(email=email, defaults={'name': name, 'is_active': True})
                if created:
                    password = get_random_string(length=8)
                    user.set_password(password)
                    user.save()
                    user_group = Group.objects.get(name=f"Data Managers")
                    user_group.user_set.add(user)
                    user_group.save()
                    print(f'Created account for user {name} with email {email} and temporary password {password}')
        self.stdout.write(self.style.SUCCESS('Done!'))
