#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 17:31:39 2020

@author: babraham
"""

from django.core.management.base import BaseCommand
#from va_explorer.va_data_management.models import VerbalAutopsy, Location
#from simple_history.utils import bulk_create_with_history
from utils.data_import import load_records_from_dataframe  
from utils import odk_api as odk
import argparse
import pandas as pd
#import re

class Command(BaseCommand):

    help = 'Pulls in CSV data from ODK and loads it into the database'

    def add_arguments(self, parser):
        parser.add_argument('--domain_name', default="127.0.0.1", help="Domain name of ODK instance")
        parser.add_argument('--project_name', default="zambia-test", help="Name of ODK project")
        parser.add_argument('--project_id', type=int, default=None, help="ODK Project ID")


    def handle(self, *args, **options):
        
        self.stdout.write("=======1. Pulling down ODK data======")
        # download records from odk
        odk_records = odk.download_responses(domain_name=options["domain_name"],\
                                             project_name=options["project_name"],\
                                             project_id=options["project_id"],\
                                             fmt='csv', export=False)
        
        self.stdout.write("=======2. Inserting ODK data into database=======")
        # load odk records into database
        load_records_from_dataframe(odk_records)
