#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 20 13:44:04 2021

@author: babraham
"""
import pandas as pd
import re
from fuzzywuzzy import fuzz

# given a query string and a list of candidates, find the candidate that most closely
# matches the query using a fuzzy matching algorithm. For more details on the
# similarity algorithm, see https://rawgit.com/ztane/python-Levenshtein/master/docs/Levenshtein.html
def fuzzy_match(search, options=None, option_df=pd.DataFrame(), threshold=75, preprocess=False, drop_terms=None, prnt=False):
    match = None
    if not pd.isnull(search):
        if not options and option_df.size == 0:
            raise ValueError("Please provide an option list or option_df (dataframe with options in 'name' column)")
        # if options not in dataframe format, create one to store them
        if option_df.size == 0:
            option_df = (pd.DataFrame({'name': options}).assign(key = lambda df: df['name'].str.lower()))
    
        # if preprocess=True, clean search term and options before comparing
        search_term = search
        if preprocess:
            if not drop_terms:
                drop_terms = ['general', 'central', 'teaching']
                
            search_term = re.sub('\_', ' ', search.lower())    
            for term in drop_terms:
                search_term = search_term.replace(f" {term}", "")
                option_df['key'] = option_df['key'].replace(f" {term}", "", regex=True)
        
        # matching
        option_df['score'] = option_df['key'].apply(lambda x: fuzz.ratio(search_term, x))
        option_df = option_df.sort_values(by='score', ascending=False)
        
        if prnt: print(option_df.head())
        
        # filter to only matches exceeding threshold
        option_df = option_df.query("score >= @threshold")
        
        if prnt: print(option_df)
        
        if option_df.size > 0:     
            match = option_df.iloc[0]['name']
    
    return match


def clean_location(loc_string, drop_terms=None):
    loc_string = re.sub('\_', ' ', loc_string.lower())    
    if drop_terms:
        for term in drop_terms:
            loc_string = loc_string.replace(f" {term.lower()}", "")
    return loc_string

# clean a list of location names by converting to lower, stripping underscores, and optionally removing drop terms. 
# can specify return_type with "list" (list of cleaned values). Otherwise, return dataframe with cleaned values in "key" column)
def clean_locations(locations, drop_terms=None, ret_type=""):

    # if locations not stored in dataframe, make one. Otherwise, assume they're in first column and rename to 'name'
    if not type(locations) is pd.DataFrame:
        locations = pd.DataFrame({'name': locations})
    else:
        locations.columns = ['name'] + locations.columns[1:]

    locations = (locations
                 .assign(key = lambda df: df['name'].str.lower().replace("\_", " ", regex=True))
                 .query("name != 'other'").dropna())
    
    if drop_terms:
        for term in drop_terms:
            locations['key'] = locations['key'].replace(f" {term.lower()}", "", regex=True)
            
    if ret_type.lower() == "list":
        return locations["key"].tolist()
    else:
        return locations
