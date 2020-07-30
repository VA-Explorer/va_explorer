from django.core.management.base import BaseCommand
from verbal_autopsy.models import Location
from django.contrib.auth import get_user_model

# TODO: This is for experimenting with the data model and should not be needed once an interface is developed

class Command(BaseCommand):

    help = 'Associates a user (specified via email address) with a location (specified via location name)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str)
        parser.add_argument('location', type=str)

    def handle(self, *args, **options):
        user = get_user_model().objects.get(email=options['email'])
        location = Location.objects.get(name=options['location'])
        location.users.add(user)
