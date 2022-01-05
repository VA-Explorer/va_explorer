from config.celery_app import app
from va_explorer.va_data_management.utils import coding


@app.task()
def run_coding_algorithms():
    results = coding.run_coding_algorithms()
    # Result of task needs to be json serializable so just make a JSON list.
    return {
        'num_coded': len(results['causes']),
        'num_total': len(results['verbal_autopsies']),
        'num_issues': len(results['issues']),
    }
