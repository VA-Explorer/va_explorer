from django.core.management.base import BaseCommand
from va_explorer.utils.coding import run_coding_algorithms

# TODO: Temporary script to run COD assignment algorithms; this should
# eventually become something that's handle with celery

class Command(BaseCommand):

    help = 'Run cause coding algorithms'

    def handle(self, *args, **options):
        result = run_coding_algorithms()
        self.stdout.write(f'Coded {result["coded_count"]} verbal autopsies (out of {result["count"]}) [{result["issue_count"]} issues]')
