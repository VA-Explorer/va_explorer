#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  6 14:01:55 2021

@author: babraham
"""
import logging

def write_va_log(logger, msg, request, logtype="info"):
    log_fns = {"info": logger.info,"debug": logger.debug}
    session_key = request.session.session_key
    msg = f"SID: {session_key} - " + msg
    log_fn = log_fns.get(logtype.lower(), logger.info)
    log_fn(msg)
    