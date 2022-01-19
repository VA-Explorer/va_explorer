from va_explorer.va_data_management.models import VerbalAutopsy, CauseOfDeath
from va_explorer.va_data_management.management.commands import run_coding_algorithms
from django.db.models import F
import pandas as pd
import time

if __name__ == '__main__':
	ti = time.time()
	COD_FNAME = 'old_cod_mapping.csv'

	# export original CODs (and corersponding VA IDs) to flat file
	va_cods = VerbalAutopsy.objects.only('id', 'causes').select_related('causes').values(va_id=F('id'), cause=F('causes__cause'))
	va_cod_df = pd.DataFrame(va_cods).dropna()
	# only export if VAs have been coded
	if not va_cod_df.empty:
		va_cod_df.to_csv(COD_FNAME, index=False)
		print(f"exported old CODs to {COD_FNAME}")
	else:
		print("No CODs found, skipping export")


	# clear CODs to re-run coding algorithm
	print('clearing old CODs...')
	CauseOfDeath.objects.all().delete()

	print('re-coding all eligible VAs')
	run_coding_algorithms()

	print(f"DONE. Total time: {time.time() - ti} seconds")


