from django.core.management.base import BaseCommand

from django.conf import settings
from va_explorer.va_data_management.models import VerbalAutopsy


class Command(BaseCommand):
    help = "Marks existing VAs as duplicate"


    def handle(self, *args, **options):
        if not settings.QUESTIONS_TO_AUTODETECT_DUPLICATES:
            self.stdout.write(
                self.style.ERROR(
                    "Error: Configuration, QUESTIONS_TO_AUTODETECT_DUPLICATES, is an empty list. \n"
                    "Please update you .env file with a list of questions by Id that will be used to autodetect "
                    "duplicates."
                )
            )
            exit()

        if not hasattr(VerbalAutopsy, 'duplicate'):
            self.stdout.write(
                self.style.ERROR(
                    "Missing required database fields in Verbal Autopsy model to mark Verbal Autopsies as duplicate."
                    "Please run latest migration to add fields."
                )
            )
            exit()

        self.stdout.write(self.style.SUCCESS("Generating unique identifiers..."))
        all_existing_vas = list(VerbalAutopsy.objects.all())
        for va in all_existing_vas:
            va.generate_unique_identifier_hash()

        self.stdout.write(self.style.SUCCESS("Unique identifiers generated!"))
        VerbalAutopsy.objects.bulk_update(all_existing_vas, ["unique_va_identifier"])

        self.stdout.write(self.style.SUCCESS("Marking existing VAs as duplicate..."))
        VerbalAutopsy.mark_duplicates()

        duplicate_count = VerbalAutopsy.objects.filter(duplicate=True).count()
        self.stdout.write(self.style.SUCCESS(f'Successfully marked {duplicate_count} existing VAs as duplicate!'))
