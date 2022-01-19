import argparse
import pandas as pd
import time
from django.core.management.base import BaseCommand
from django.db.models import F
from va_explorer.va_data_management.utils.coding import run_coding_algorithms
from va_explorer.va_data_management.models import VerbalAutopsy, CauseOfDeath


class Command(BaseCommand):

    help = 'Run cause coding algorithms'

    def add_arguments(self, parser):
        # whether or not to overwrite existing CODs - if True, will clear all CODs before running
        parser.add_argument('--overwrite', type=bool, nargs='?', default=False)
        parser.add_argument('--cod_fname', type=str, nargs='?', default='old_cod_mapping.csv')

    def handle(self, *args, **options):
        ti = time.time()
        if options['overwrite']:
            self.clear_and_save_old_cods(**options)

        print('coding all eligible VAs... ')
        results = run_coding_algorithms()
        num_coded = len(results['causes'])
        num_total = len(results['verbal_autopsies'])
        num_issues = len(results['issues'])
        self.stdout.write(f'DONE. Total time: {time.time() - ti} secs')
        self.stdout.write(f'Coded {num_coded} verbal autopsies (out of {num_total}) [{num_issues} issues]')

    def clear_and_save_old_cods(self, *args, **kwargs):
        
        print('clearing old CODs...')
        cod_fname = kwargs.get('cod_fname', 'old_cod_mapping.csv')
        # export original CODs (and corersponding VA IDs) to flat file
        va_cods = VerbalAutopsy.objects.only('id', 'causes').select_related('causes').values(va_id=F('id'), cause=F('causes__cause'))
        va_cod_df = pd.DataFrame(va_cods).dropna()
        # only export if VAs have been coded
        if not va_cod_df.empty:
            va_cod_df.to_csv(cod_fname, index=False)
            print(f'exported {va_cod_df.shape[0]} old CODs to {cod_fname}')
        else:
            print('No CODs found, skipping export')

        # clear CODs to re-run coding algorithm
        CauseOfDeath.objects.all().delete()
