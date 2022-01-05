from django.core.management.base import BaseCommand
from va_explorer.va_data_management.models import VerbalAutopsy, CauseOfDeath, dhisStatus,cod_codes_dhis
from django.forms.models import model_to_dict
from io import StringIO
from collections import OrderedDict
import dateutil.parser,os,requests,collections
import csv, environ
# from . import dhis as dhis
import openva_pipeline.dhis as dhis
import pandas as pd
import numpy as np

# TODO: Temporary script to run COD assignment algorithms; this should
# eventually become something that's handle with celery

class Command(BaseCommand):
    help = 'Run dhis code'
    def generateEntityAttribute(self,data):
        dataT = data.transpose()
        dataT["Attribute"] = dataT.index
        dmain = dataT[{"Attribute", 0}]
        dmain["ID"] = str(dmain[0][0])
        dmain = dmain.rename(columns={0: "Value"})
        for i in range(1, dataT.shape[1] - 1):
            uuid = dataT[i][0]
            dg = dataT[{"Attribute", i}]
            dg["ID"] = dg[i][0]
            dg = dg.rename(columns={i: "Value"})
            dg = dg[1:]
            dmain = dmain.append(dg)
        dmain = dmain[1:]
        dmain = dmain[["ID", "Attribute", "Value"]]
        return dmain

    def clearFolder(self,dir):
        for file in os.scandir(dir):
            os.remove(file.path)

    def handle(self, *args, **options):
        env = environ.Env()
        # DHIS2 VARIABLES
        DHIS2_URL = env("DHIS2_URL")
        DHIS2_USER = env("DHIS2_USER")
        DHIS2_PASS = env("DHIS2_PASS")
        DHIS2_ORGUNIT = env("DHIS2_ORGUNIT")

        metadatacode = "InterVA5|5|Custom|1|2016 WHO Verbal Autopsy Form|v1_5_1"

        #auth = (DHIS2_USER, DHIS2_PASS)
        #va_in_dhis2 = self.getPushedVA('sv91bCroFFx', auth)
        #dhisdata = [int(i) for i in va_in_dhis2]

        # Load all verbal autopsies that have been pushed to dhis2
        dhisdata = dhisStatus.objects.values_list("verbalautopsy_id", flat=True)

        #to subset few rows,add at the end [:10] for 10 rows etc..
        #exclude vas that have no dhis2 status; not pushed
        vadata = VerbalAutopsy.objects.filter(causes__isnull=False).exclude(id__in=dhisdata) #[:30]

        #ceate a list of available VA IDs to help during filtering queries
        va_not_in_dhis = list()
        for va in vadata:
            va_not_in_dhis.append(va.id)
        va_not_in_dhis = [str(i) for i in va_not_in_dhis]

        if len(va_not_in_dhis)>0:

            #load VAs with causes
            cod = CauseOfDeath.objects.filter(verbalautopsy_id__in=va_not_in_dhis).values()
            cod = pd.DataFrame.from_records(cod)
            cod = cod[{"verbalautopsy_id","cause"}]

            # Get into CSV format, also prefixing keys with - as expected by pyCrossVA (e.g. Id10424 becomes -Id10424)
            va_data = [model_to_dict(va) for va in vadata]
            vadf = pd.DataFrame.from_records(va_data)

            codva = cod.join(vadf, how='outer')

            va_data = [dict([(f'-{k}', v) for k, v in d.items()]) for d in va_data]
            va_data_csv = pd.DataFrame.from_records(va_data).to_csv()

            # Transform to algorithm format using the pyCrossVA web service
            transform_url = 'http://127.0.0.1:5001/transform?input=2016WHOv151&output=InterVA5'
            transform_response = requests.post(transform_url, data=va_data_csv)

            # We need to convert the resulting CSV to JSON
            transform_response_reader = csv.DictReader(StringIO(transform_response.text))
            algorithm_input_rows = []
            for row in transform_response_reader:
                # Replace blank key with ID and append to list for later jsonification
                algorithm_input_rows.append(OrderedDict([('ID', v) if k == '' else (k, v) for k, v in row.items()]))

            crossva = pd.DataFrame(algorithm_input_rows)
            crossva = crossva.replace("0.0",".").replace("1.0","y")

            crossva['ID'] = va_not_in_dhis

            crossvacod = cod.join(crossva, how='outer')
            crossvacod['Cause of Death']= crossvacod['cause']
            crossvacod['Metadata'] = metadatacode
            crossvacod = crossvacod.drop(['verbalautopsy_id','cause'], axis=1)

            eadata = self.generateEntityAttribute(crossvacod)

            #append a letter A to IDs; for some reason it was failing having numeric IDs
            # producing KeyError trying to compare string/integer numbers
            eadata['ID'] =["A"+str(i) for i in eadata['ID']]
            if os.path.exists("OpenVAFiles"):
                eadata.to_csv("OpenVAFiles/entityAttributeValue.csv", index=False)
            else:
                os.makedirs("OpenVAFiles")
                eadata.to_csv("OpenVAFiles/entityAttributeValue.csv", index=False)

            codva['metadataCode'] = metadatacode
            codva['odkMetaInstanceID'] = codva['id']
            vasubset= codva[{"id","Id10019","Id10021","Id10023","ageInYears2","cause","metadataCode","odkMetaInstanceID"}]
            vasubset = vasubset.rename(columns={"Id10019":"sex", "Id10021":"dob",
                                                "Id10023":"dod","ageInYears2":"age",
                                                "cause":"cod"})
            vasubset = vasubset[['id', 'sex', 'dob', 'dod', 'age', 'cod', 'metadataCode','odkMetaInstanceID']]


            storagev = vasubset.join(crossva, how='outer')
            storagev= storagev.drop(['ID'], axis=1)
            storagev.to_csv("OpenVAFiles/recordStorage.csv", index=False)

            # Ensure all variables are formatted as required
            vadata = pd.read_csv("OpenVAFiles/recordStorage.csv")
            vadata["age"] = vadata["age"].astype(float)
            vadata['dod'][vadata.dod.isnull()] = '1900-01-01'
            vadata['dob'][vadata.dob.isnull()] = '1900-01-01'
            vadata['id'] = ["A" + str(i) for i in vadata['id']]
            for i in range(len(vadata["sex"])):
                vadata["dob"][i] = dateutil.parser.parse(vadata["dob"][i]).date().strftime("%Y-%m-%d")
                vadata["dod"][i] = dateutil.parser.parse(vadata["dod"][i]).date().strftime("%Y-%m-%d")
                vadata["cod"][i] = vadata["cod"][i].strip()
                vadata["metadataCode"][i] =  metadatacode
            vadata.to_csv("OpenVAFiles/recordStorage.csv", index=False)

            # dhis settings
            ntDHIS = collections.namedtuple("ntDHIS",
                                            ["dhisURL",
                                             "dhisUser",
                                             "dhisPassword",
                                             "dhisOrgUnit"]
                                            )
            settingsDHIS = ntDHIS(DHIS2_URL, DHIS2_USER, DHIS2_PASS, DHIS2_ORGUNIT)

            CODCodes =  cod_codes_dhis.objects.filter(codsource="WHO").values()
            queryCODCodes = pd.DataFrame.from_records(CODCodes)
            queryCODCodes = queryCODCodes[{"codname", "codcode"}]

            dhisCODCodes = dict(zip(queryCODCodes.codname, queryCODCodes.codcode))

            dhisCODCodes = {}
            argsDHIS = [settingsDHIS, dhisCODCodes]

            # execute pipeline
            pipelineDHIS = dhis.DHIS(argsDHIS,"")

            apiDHIS = pipelineDHIS.connect()
            self.clearFolder("DHIS/blobs/")
            postLog = pipelineDHIS.postVA(apiDHIS)
            self.clearFolder("DHIS/blobs/")
            if postLog['response']['status']=='SUCCESS' and postLog['response']['imported']==len(va_not_in_dhis):
                numPushed = postLog['response']['imported']
                numTotal = postLog['response']['total']
                status = postLog['response']['status']
            self.stdout.write(f' Uploaded {numPushed} out of {numTotal} verbal autopsies ')

        else:
            numPushed=0
            numTotal=0
            status="Nothing to Post"

        self.syncDHISStatus()

        return numPushed,numTotal,status

    def syncDHISStatus(self):
        env = environ.Env()

        # DHIS2 VARIABLES
        DHIS2_USER = env("DHIS2_USER")
        DHIS2_PASS = env("DHIS2_PASS")

        auth = (DHIS2_USER, DHIS2_PASS)
        va_in_dhis2 = self.getPushedVA('sv91bCroFFx', auth)
        va_in_dhis2 = [str(i) for i in va_in_dhis2]

        #print(va_in_dhis2)
        dhisdata = dhisStatus.objects.filter(verbalautopsy_id__isnull=False).values_list('vaid',flat=True)
        dhisdata = list(dhisdata)
        dhisdata = [str(i) for i in dhisdata]

        #remove orphaned items deleted in dhis2
        for x in dhisdata:
            if x not in va_in_dhis2:
                ds = dhisStatus.objects.get(vaid=x)
                ds.delete()

        dhisdata = dhisStatus.objects.filter(verbalautopsy_id__isnull=False).values_list('vaid', flat=True)
        dhisdata = list(dhisdata)
        dhisdata = [str(i) for i in dhisdata]

        toinsert = np.setdiff1d(va_in_dhis2, dhisdata)
        toinsert = list(toinsert)

        for item in toinsert:
            ds = dhisStatus.objects.create(vaid=item,verbalautopsy_id=int(item))
            ds.save()

    def getEventsValues(self,prg, auth):
        env = environ.Env()

        # DHIS2 VARIABLES
        DHIS2_URL = env("DHIS2_URL")
        DHIS2_ORGUNIT = env("DHIS2_ORGUNIT")
        url = DHIS2_URL+'/api/events?pageSize=0&program=' + prg + '&orgUnit=' + DHIS2_ORGUNIT + '&totalPages=true'
        response = requests.get(url, auth=auth)
        jn = response.json()
        return jn['pager']['total']

    def getPushedVA(self,prg, auth):
        env = environ.Env()
        # DHIS2 VARIABLES
        DHIS2_URL = env("DHIS2_URL")
        DHIS2_ORGUNIT = env("DHIS2_ORGUNIT")

        eventsnum = self.getEventsValues(prg, auth)
        url = DHIS2_URL+'/api/events?pageSize=' + format(eventsnum,'0') + '&program=' + prg + '&orgUnit=' + DHIS2_ORGUNIT + '&totalPages=true'
        r = requests.get(url, auth=auth)
        jn = r.json()
        list1 = list()
        for i in range(eventsnum):
            cols = len(jn['events'][i]['dataValues'])
            for j in range(cols):
                if jn['events'][i]['dataValues'][j]['dataElement'] == 'LwXZ2dZmJb0':
                    txt = jn['events'][i]['dataValues'][j]['value']
                    list1.append(txt)
        return list1

