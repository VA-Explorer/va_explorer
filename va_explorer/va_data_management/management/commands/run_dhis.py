import csv
import os
from collections import OrderedDict, namedtuple
from io import StringIO

import dateutil.parser
import numpy as np
import pandas as pd
import requests
from django.core.management.base import BaseCommand
from django.forms.models import model_to_dict

from va_explorer.dhis_manager.dhis import DHIS
from va_explorer.va_data_management.models import (
    CauseOfDeath,
    CODCodesDHIS,
    DhisStatus,
    VerbalAutopsy,
)

DHIS_USER = os.environ.get("DHIS_USER")
DHIS_PASS = os.environ.get("DHIS_PASS")
DHIS_HOST = os.environ.get("DHIS_HOST")
DHIS_ORGUNIT = os.environ.get("DHIS_ORGUNIT")

DHIS2_HOST = os.environ.get("DHIS2_URL", "http://127.0.0.1:5002")
SSL_VERIFY = (
    False
    if DHIS2_HOST.startswith("https://localhost")
    else os.environ.get("DHIS2_SSL_VERIFY", "TRUE").lower() in ("true", "1", "t")
)

# TODO: Temporary script to run COD assignment algorithms; this should
# eventually become something that's handle with celery


class Command(BaseCommand):
    help = "Run dhis code"

    def generate_entity_attribute(self, data):
        data_transpose = data.transpose()
        data_transpose["Attribute"] = data_transpose.index
        data_main = data_transpose[{"Attribute", 0}]
        data_main["ID"] = str(data_main[0][0])
        data_main = data_main.rename(columns={0: "Value"})
        for i in range(1, data_transpose.shape[1] - 1):
            data_group = data_transpose[{"Attribute", i}]
            data_group["ID"] = data_group[i][0]
            data_group = data_group.rename(columns={i: "Value"})
            data_group = data_group[1:]
            data_main = data_main.append(data_group)
        data_main = data_main[1:]
        data_main = data_main[["ID", "Attribute", "Value"]]
        return data_main

    def clear_folder(self, dir):
        for file in os.scandir(dir):
            os.remove(file.path)

    def handle(self, *args, **options):
        _ = (args, options)  # unused

        metadatacode = "InterVA5|5|Custom|1|2016 WHO Verbal Autopsy Form|v1_5_1"

        # Load all verbal autopsies that have been pushed to dhis2
        dhis_data = DhisStatus.objects.values_list("verbalautopsy_id", flat=True)

        # to subset few rows,add at the end [:10] for 10 rows etc..
        # exclude vas that have no dhis2 status; not pushed
        va_data = VerbalAutopsy.objects.filter(causes__isnull=False).exclude(
            id__in=dhis_data
        )  # [:30]

        # create a list of available VA IDs to help during filtering queries
        va_not_in_dhis = []
        for va in va_data:
            va_not_in_dhis.append(va.id)
        va_not_in_dhis = [str(i) for i in va_not_in_dhis]

        if len(va_not_in_dhis) > 0:
            # load VAs with causes
            cod = CauseOfDeath.objects.filter(
                verbalautopsy_id__in=va_not_in_dhis
            ).values()
            cod = pd.DataFrame.from_records(cod)
            cod = cod[{"verbalautopsy_id", "cause"}]

            # Get into CSV format, also prefixing keys with - as expected by
            # pyCrossVA (e.g. Id10424 becomes -Id10424)
            va_data = [model_to_dict(va) for va in va_data]
            va_df = pd.DataFrame.from_records(va_data)

            cod_va = cod.join(va_df, how="outer")

            va_data = [{f"-{k}": v for k, v in d.items()} for d in va_data]
            va_data_csv = pd.DataFrame.from_records(va_data).to_csv()

            # Transform to algorithm format using the pyCrossVA web service
            # TODO: Check that this service is running and provide a warning if
            # it isn't because this will cause failure
            # TODO: Handle failure so that UI doesn't crash
            # TODO: This can take absurdly long, lets make it into a batch async job
            transform_url = (
                "http://127.0.0.1:5001/transform?input=2016WHOv151&output=InterVA5"
            )
            transform_response = requests.post(
                transform_url, data=va_data_csv, verify=SSL_VERIFY
            )

            # We need to convert the resulting CSV to JSON
            transform_response_reader = csv.DictReader(
                StringIO(transform_response.text)
            )
            algorithm_input_rows = []
            for row in transform_response_reader:
                # Replace blank key with ID and append to list for later jsonification
                algorithm_input_rows.append(
                    OrderedDict(
                        [("ID", v) if k == "" else (k, v) for k, v in row.items()]
                    )
                )

            crossva_data = pd.DataFrame(algorithm_input_rows)
            crossva_data = crossva_data.replace("0.0", ".").replace("1.0", "y")

            crossva_data["ID"] = va_not_in_dhis

            crossva_cod = cod.join(crossva_data, how="outer")
            crossva_cod["Cause of Death"] = crossva_cod["cause"]
            crossva_cod["Metadata"] = metadatacode
            crossva_cod = crossva_cod.drop(["verbalautopsy_id", "cause"], axis=1)

            entity_atr_data = self.generate_entity_attribute(crossva_cod)

            # append a letter A to IDs; for some reason it fails having numeric IDs
            # producing KeyError trying to compare string/integer numbers
            entity_atr_data["ID"] = ["A" + str(i) for i in entity_atr_data["ID"]]
            if os.path.exists("OpenVAFiles"):
                entity_atr_data.to_csv(
                    "OpenVAFiles/entityAttributeValue.csv", index=False
                )
            else:
                os.makedirs("OpenVAFiles")
                entity_atr_data.to_csv(
                    "OpenVAFiles/entityAttributeValue.csv", index=False
                )

            cod_va["metadataCode"] = metadatacode
            cod_va["odkMetaInstanceID"] = cod_va["id"]
            va_subset = cod_va[
                {
                    "id",
                    "Id10019",
                    "Id10021",
                    "Id10023",
                    "ageInYears2",
                    "cause",
                    "metadataCode",
                    "odkMetaInstanceID",
                }
            ]
            va_subset = va_subset.rename(
                columns={
                    "Id10019": "sex",
                    "Id10021": "dob",
                    "Id10023": "dod",
                    "ageInYears2": "age",
                    "cause": "cod",
                }
            )
            va_subset = va_subset[
                [
                    "id",
                    "sex",
                    "dob",
                    "dod",
                    "age",
                    "cod",
                    "metadataCode",
                    "odkMetaInstanceID",
                ]
            ]

            vas_to_store = va_subset.join(crossva_data, how="outer")
            vas_to_store = vas_to_store.drop(["ID"], axis=1)
            vas_to_store.to_csv("OpenVAFiles/recordStorage.csv", index=False)

            # Ensure all variables are formatted as required
            va_data = pd.read_csv("OpenVAFiles/recordStorage.csv")
            va_data["age"] = va_data["age"].astype(float)
            va_data["dod"][va_data.dod.isna()] = "1900-01-01"
            va_data["dob"][va_data.dob.isna()] = "1900-01-01"
            va_data["id"] = ["A" + str(i) for i in va_data["id"]]
            for i in range(len(va_data["sex"])):
                va_data["dob"][i] = (
                    dateutil.parser.parse(va_data["dob"][i]).date().strftime("%Y-%m-%d")
                )
                va_data["dod"][i] = (
                    dateutil.parser.parse(va_data["dod"][i]).date().strftime("%Y-%m-%d")
                )
                va_data["cod"][i] = va_data["cod"][i].strip()
                va_data["metadataCode"][i] = metadatacode
            va_data.to_csv("OpenVAFiles/recordStorage.csv", index=False)

            # dhis settings
            ntDHIS = namedtuple(
                "ntDHIS", ["dhisURL", "dhisUser", "dhisPassword", "dhisOrgUnit"]
            )
            settings_dhis = ntDHIS(DHIS_HOST, DHIS_USER, DHIS_PASS, DHIS_ORGUNIT)

            cod_codes = CODCodesDHIS.objects.filter(codsource="WHO").values()
            query_cod_codes = pd.DataFrame.from_records(cod_codes)
            query_cod_codes = query_cod_codes[{"codname", "codcode"}]

            dhis_cod_codes = dict(
                zip(query_cod_codes.codname, query_cod_codes.codcode, strict=True)
            )

            dhis_cod_codes = {}
            args_dhis = [settings_dhis, dhis_cod_codes]

            # execute pipeline
            pipeline_dhis = DHIS(args_dhis, "")

            api_dhis = pipeline_dhis.connect()
            self.clearFolder("DHIS/blobs/")
            post_log = pipeline_dhis.postVA(api_dhis)
            self.clearFolder("DHIS/blobs/")
            if post_log["response"]["status"] == "SUCCESS" and post_log["response"][
                "imported"
            ] == len(va_not_in_dhis):
                num_pushed = post_log["response"]["imported"]
                num_total = post_log["response"]["total"]
                status = post_log["response"]["status"]
            self.stdout.write(
                f" Uploaded {num_pushed} out of {num_total} verbal autopsies "
            )

        else:
            num_pushed = 0
            num_total = 0
            status = "Nothing to Post"

        self.sync_dhis_status()

        return num_pushed, num_total, status

    def sync_dhis_status(self):
        auth = (DHIS_USER, DHIS_PASS)
        va_in_dhis = self.get_pushed_va("sv91bCroFFx", auth)
        va_in_dhis = [str(i) for i in va_in_dhis]

        dhis_data = DhisStatus.objects.filter(
            verbalautopsy_id__isnull=False
        ).values_list("vaid", flat=True)
        dhis_data = list(dhis_data)
        dhis_data = [str(i) for i in dhis_data]

        # remove orphaned items deleted in dhis2
        for x in dhis_data:
            if x not in va_in_dhis:
                ds = DhisStatus.objects.get(vaid=x)
                ds.delete()

        dhis_data = DhisStatus.objects.filter(
            verbalautopsy_id__isnull=False
        ).values_list("vaid", flat=True)
        dhis_data = list(dhis_data)
        dhis_data = [str(i) for i in dhis_data]

        to_insert = np.setdiff1d(va_in_dhis, dhis_data)
        to_insert = list(to_insert)

        for item in to_insert:
            ds = DhisStatus.objects.create(vaid=item, verbalautopsy_id=int(item))
            ds.save()

    def get_events_values(self, prg, auth):
        url = (
            DHIS_HOST
            + "/api/events?pageSize=0&program="
            + prg
            + "&orgUnit="
            + DHIS_ORGUNIT
            + "&totalPages=true"
        )
        response = requests.get(url, auth=auth)
        jn = response.json()
        return jn["pager"]["total"]

    def get_pushed_va(self, prg, auth):
        # default to hardcoded value used in VA DHIS program
        prg = prg if prg else "sv91bCroFFx"

        events_num = self.get_events_values(prg, auth)
        url = (
            DHIS_HOST
            + "/api/events?pageSize="
            + format(events_num, "0")
            + "&program="
            + prg
            + "&orgUnit="
            + DHIS_ORGUNIT
            + "&totalPages=true"
        )
        r = requests.get(url, auth=auth)
        jn = r.json()
        list1 = []
        for i in range(events_num):
            cols = len(jn["events"][i]["dataValues"])
            for j in range(cols):
                if jn["events"][i]["dataValues"][j]["dataElement"] == "LwXZ2dZmJb0":
                    txt = jn["events"][i]["dataValues"][j]["value"]
                    list1.append(txt)
        return list1
