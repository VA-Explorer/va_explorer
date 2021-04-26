#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 21 09:52:20 2021

@author: babraham
"""

import logging
import logging.config

#====Logging Config=============#
FORMAT = "[%(asctime)s - %(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
LOGFILE = "va_explorer/logs/data_ingest.log"

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(name)-12s %(levelname)-8s %(message)s'
        },
        'file': {
            'format': FORMAT
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'file',
            'filename': LOGFILE
        }
    },
    'loggers': {
        'data_ingest': {
            'level': 'DEBUG',
            'handlers': ['file']
        }
    }
})
