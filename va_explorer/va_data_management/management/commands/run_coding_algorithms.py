from django.core.management.base import BaseCommand
from va_explorer.va_data_management.utils.coding import run_coding_algorithms


class Command(BaseCommand):

    help = 'Run cause coding algorithms'

    def handle(self, *args, **options):
        results = run_coding_algorithms()
        num_coded = len(results['causes'])
        num_total = len(results['verbal_autopsies'])
        num_issues = len(results['issues'])

        self.stdout.write(f'Coded {num_coded} verbal autopsies (out of {num_total}) [{num_issues} issues]')
