#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 21:18:43 2020

@author: babraham
"""

import requests
import pandas as pd
import numpy as np
from numpy.random import choice
import xml.etree.ElementTree as ET
import uuid
import json
import re
import zipfile
from io import BytesIO


#======Main utilities=============#
## Demo files
# xml_file = "va_explorer/va_explorer/demo/va_xml_template.xml"
# sample_csv = "va_explorer/va_explorer/demo/sample_records_to_load_into_odk.csv"
def upload_sample_to_odk(form_template_file, sample_csv_file, token=None,\
                                  project_id=None, project_name=None, domain_name="127.0.0.1"):
    assert(project_name or project_id)
    if not token:
        print("No token provided. Please provide credentials to obtain auth token.")
        token = get_odk_login_token(domain_name)
    
    # build forms
    va_forms = generate_responses_from_sample(form_template_file, sample_csv_file)
    
    # submit forms
    submit_forms_to_odk(va_forms, domain_name=domain_name, project_name=project_name,\
                              project_id=project_id, token=token)
    
    #=======download form responses from odk===#
# TODO ### CHANGE THIS BACK TO project_name=None AFTER DEMO
def download_responses(form_url=None, domain_name="127.0.0.1", \
                        project_name='zambia-test', project_id=None, token=None, fmt='csv', export=False):
    forms = None
    if not token:
        token = get_odk_login_token(domain_name)
        

    assert(form_url or ((project_id or project_name) and domain_name))
    
    if not form_url:
        form_url = get_odk_form_url(domain_name=domain_name, project_id=project_id,\
                                    project_name=project_name, token=token)
    if fmt == 'json':
        form_download_url = re.sub('/versions/.*?\.xml', '.svc/Submissions', form_url)
        response = requests.get(form_download_url,  headers=token, verify=False).json()
        if 'value' in response.keys():
            forms = response['value']
            print(f"downloaded {len(forms)} forms from odk")
    elif fmt == 'csv':
        form_download_url = re.sub('/versions/.*?\.xml', '/submissions.csv.zip', form_url)
        res = requests.get(form_download_url, headers=token, verify=False)
        filebytes = BytesIO(res.content)
        myzipfile = zipfile.ZipFile(filebytes)
        csv_file = myzipfile.namelist()[0]
        forms = pd.read_csv(BytesIO(myzipfile.open(csv_file).read()))
        forms.columns = [c.split('-')[-1] for c in forms.columns]

    else:
        raise(TypeError("Please provide valid format (fmt): (csv, json)"))
        
    if export:
        fname = f"../va_explorer_resources/odk_download.{fmt}"
        if fmt == 'json':
            with open(fname, "w") as out:
                out.write(json.dumps(forms))
        else:
            forms.to_csv(fname, index=False)
        print(f"downloaded odk data and wrote to {fname}")
   
    return forms



#=============Authentication=====================#
# TODO: FIND BETTER SOLUTION FOR DEFAULT CREDENTIALS    
# get a token to authenticate future odk operations
    #sample_res = {'token': '90SzQyN1wpj1eECuMCANXnNhsOpVD!qrKDoVy584mNK4r1GiYwBKuQfWEwYRCzC!',
    # 'csrf': '5L36Y5OsNtxrxoJZBm5AzdXSc$hVqhQlMhEqGjGulG8g6xqOk$FvlMa$kELTRuC5',
    # 'expiresAt': '2020-11-13T02:23:02.953Z',
    # 'createdAt': '2020-11-12T02:23:02.956Z'}
    # sample sessions url: #url = 'https://private-anon-f8a973882b-odkcentral.apiary-mock.com/v1/sessions'
def get_odk_login_token(domain_name="127.0.0.1", email="admin@example.com", password="Password1", return_header=True):
    url = f"https://{domain_name}/v1/sessions"
#    if not email:
#        email = input("email address: ")
#    if not password:
#        password = input("password: ")
    creds = json.dumps({"email": email, "password": password}) 
    headers = {"Content-Type": "application/json"}
    res = requests.post(url, headers=headers, data=creds, verify=False)
    token = res.json()['token']
    return {"Authorization": f"Bearer {token}"} if return_header else token        

# get project id for project name of project created with odk central
def get_odk_project_id(project_name, domain_name="127.0.0.1", token=None):
    project_id = None
    if not token:
        print("No token provided. Please provide credentials to obtain auth token.")
        token = get_odk_login_token(domain_name)
    base_url = f"https://{domain_name}/v1"
    projs = json.loads(requests.get(f"{base_url}/projects/",
                                 headers=token, verify=False).text)
    proj_df = pd.DataFrame.from_records(projs)
    if proj_df.size == 0:
        print("ERROR: No active projects found")
        
    project_lookup = proj_df[proj_df['name'] == project_name]
    if project_lookup.size == 0:
        print(f"ERROR: Couldnt find project named {project_name}. Here are all active projects: ")
        print(proj_df)
    else:
        project_id = project_lookup['id'].values[0]
    return project_id

#=============Form informationß=====================#

# download a project's form xml template
def get_odk_form_url(domain_name="127.0.0.1", token=None, project_id=None, project_name=None):
    base_url = f"https://{domain_name}/v1"
    form_url = None
    # must provide project name or project id for function to work
    assert(project_name or project_id)
    if not token:
        print("No token provided. Please provide credentials to obtain auth token.")
        token = get_odk_login_token(domain_name)
        
    # get project id if only project name provided.
    if not project_id:
        project_id = get_odk_project_id(project_name, domain_name, token)
    
    # get latest form available for current project
    project_forms_url = f"{base_url}/projects/{project_id}/forms"
    forms = requests.get(project_forms_url, headers=token, verify=False).json()
    if len(forms) == 0:
        raise(Exception("ERROR: no forms found for peojct"))
    else:
        # example form url: "https://192.168.99.129/v1/projects/2/forms/va_who_v1_5_2/versions/2019101701.xml"
        form = forms[-1]
        form_string = f"{form['xmlFormId']}/versions/{form['version']}.xml"
        form_url = f"{project_forms_url}/{form_string}"
    return form_url

def download_odk_form(odk_form_url, domain_name='127.0.0.1', token=None):
    if not token:
        print("No token provided. Please provide credentials to obtain auth token.")
        token = get_odk_login_token(domain_name)
    form_text = requests.get(odk_form_url, headers=token, verify=False).text
    return form_text

#===============form filling================#
# fill out xml form given an xml template and sample data
# usage: 
# xml = open(xml_template.xml)
# vf = va_form(xml)
# vf.fill_xml_from_rec(sample_data)

# generate N forms based on form template and pre-existing csv responses. 
    # ex. form template file: va_xml_template.xml
    # ex. csv_file: 'cod_analysis/new_va_sample.csv'
def generate_responses_from_sample(form_template_file, sample_csv_file, randomize=False, N=100):
    xml = open(form_template_file, 'r').read()
    sample_va_df = pd.read_csv(sample_csv_file)
        
    # if columns start with -, remove them for now. Will add back downstream
    sample_va_df.columns = [re.sub('^\-', '', c) for c in sample_va_df.columns]
    sample_va_df.columns = [f"-{c.split('-')[-1]}" for c in sample_va_df.columns]
    

    # If randomize is True, generate random sample of size N. Otherwise, use all provided records 
    if randomize:
        va_form_df = sample_va_df.sample(N, replace=True).reset_index()

        fields  = {
            "age": "ageInYears",
            "sex": "Id10019",
            "place of death": "Id10058",
            "date": "Id10023"
        }
    
        for field in fields.keys():
            field_id = fields[field]
            va_form_df[field_id] = choice(sample_va_df[field_id], replace=True, size=N)
    
    else:
        va_form_df = sample_va_df
    
    # convert each form's data into dictionary
    recs = va_form_df.to_dict(orient='index')
    # create xml form for each data record
    form_objects = []
    for k, rec in recs.items():
        try:
            form = va_form(xml)
            form.fill_xml_from_rec(rec, prnt=False)
            form_objects.append(form)
        except:
            print(f"error filling form for record {k}")
    
    return form_objects

        
class va_form(object):
    tree=None    
    def __init__(self, xml=None, xml_file=None):
        if xml:
            self.tree = ET.fromstring(xml)
        elif xml_file:
            self.tree = ET.parse(xml_file)
        else:
            self.tree = ET.Element()
        
        # if no meta tag, create one and attach to root
        if not self.tree.find('meta'):
            meta = ET.Element('meta')
            root = self.tree.getroot() 
            # if no instanceID tag, reate one and attach to meta first
            if not self.tree.find('meta/instanceID'):
                instanceID = ET.Element('instanceID')
                new_elem = ET.SubElement(meta, instanceID)
            new_elem = ET.SubElement(root, meta)
        # add an instanceID (path: meta/instanceID)
        uuid = self.generate_instanceID()
        self.tree.find("meta/instanceID").text = uuid
    
    def fill_xml_from_rec(self, rec, prnt=False, ret_leaves=False):
        leaves = {}
        def _get_leaf_nodes(current_node):
            if current_node is not None:
                children = list(current_node)
                if not children:
                    question = f"-{current_node.tag}"
                    question_value = rec.get(question, "")
                    #question_value = rec[question]
                    if question_value:
                        if prnt: print((type(question_value), question, question_value))
                        if type(question_value) is str:
                            current_node.text = question_value
                        elif not np.isnan(question_value):
                            current_node.text = str(question_value)

                    leaves[question] = current_node.text
                for child in current_node:
                    _get_leaf_nodes(child)
        _get_leaf_nodes(self.tree)
        if ret_leaves: return leaves
    
    def tostring(self):
        return ET.tostring(self.tree)
    
    def export(self, filename):
        with open(filename, 'wb') as out:
            out.write(self.tostring())
    def generate_instanceID(self):
        uid = str(uuid.uuid4())
        return f"uuid:{uid}"
            

#============form submission=============#

## read in xml template for submission generation
# sample form (from odk dump, obtained using following code):
    #import psycopg2
    #conn = psycopg2.connect("dbname=odk_test")
    #cursor = conn.cursor()
    #res = pd.read_sql("SELECT * from submission_defs;", conn)
# create va form object and populate with xml template
#form_submit_url = "https://192.168.99.129/v1/projects/2/forms/va_who_v1_5_2/submissions"

def submit_forms_to_odk(form_objs, form_submit_url=None, domain_name="127.0.0.1", \
                        project_name=None, project_id=None, token=None):
    if not token:
        raise(Exception("No token provided. Please generate one with get_odk_login_token(domain_name)."))
    
    assert(form_submit_url or ((project_id or project_name) and domain_name))
    if not form_submit_url: 
        form_url = get_odk_form_url(domain_name=domain_name, project_id=project_id,\
                                    project_name=project_name, token=token)
        form_submit_url = re.sub('versions/.*?\.xml', 'submissions', form_url)
    
    responses = [submit_form_to_odk(form_submit_url, f.tostring(), token) for f in form_objs]

# helper method to submit a single va form to odk
def submit_form_to_odk(form_submit_url, form_xml, token=None):     
    if not token:
        raise(Exception("No token provided. Please generate one with get_odk_login_token(domain_name)."))
   
    headers = token if type(token) is dict else {"Authorization": f"Bearer {token}"}
    headers['Content-Type'] = 'application/xml'
    return requests.post(form_submit_url, headers=headers, data=form_xml, verify=False)






