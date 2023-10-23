"""
NOTICE: [Original Software](https://github.com/verbal-autopsy-software/openva_pipeline)
Changes: Replaced references to custom exception DHISError with generic Exception
Changes: Applied project linting/styling to code
See project LICENSE file for the full license text
"""

import csv
import datetime
import json
import os
import re
import sqlite3
from math import isnan

import requests
from pandas import isna, read_csv


class API:
    """This class provides methods for interacting with the DHIS2 API.

    This class is called by an instance of the :class:`DHIS <DHIS>` to retrieve
    information from and post verbal autopsy records (and results) to a
    DHIS2 server that has the Verbal Autopsy program installed.

    :param dhisURL: Web address for DHIS2 server (e.g., "play.dhis2.org/demo").
    :type dhisURL: string
    :param dhisUser: Username for DHIS2 account.
    :type dhisUser: string
    :param dhisPassword: Password for DHIS2 account.
    :type dhisPassword: string
    :raises: Exception
    """

    def __init__(self, dhisURL, dhisUser, dhisPass):
        if "/api" in dhisURL:
            raise Exception(
                "Please do not specify /api/ in the server argument: \
              e.g. --server=play.dhis2.org/demo"
            )
        if dhisURL.startswith("localhost") or dhisURL.startswith("127.0.0.1"):
            dhisURL = f"http://{dhisURL}"
        elif not dhisURL.startswith("https://") and not dhisURL.startswith("http://"):
            dhisURL = f"https://{dhisURL}"
        self.auth = (dhisUser, dhisPass)
        self.url = f"{dhisURL}/api"  # possible new parameter

    def get(self, endpoint, params=None):
        """GET method for DHIS2 API.

        :rtype: dict
        """

        url = f"{self.url}/{endpoint}.json"
        if not params:
            params = {}
        params["paging"] = False
        try:
            r = requests.get(url=url, params=params, auth=self.auth)
            if r.status_code != 200:
                raise Exception(f"HTTP Code: {r.status_code}")
            else:
                return r.json()
        except requests.RequestException as err:
            raise Exception(str(requests.RequestException)) from err

    def post(self, endpoint, data):
        """POST method for DHIS2 API.

        :rtype: dict
        """

        url = f"{self.url}/{endpoint}.json"
        try:
            r = requests.post(url=url, json=data, auth=self.auth)
            if r.status_code not in range(200, 206):
                raise Exception(
                    "Problem with API.post..."
                    + f"HTTP Code: {r.status_code}..."
                    + str(r.text)
                )
            else:
                return r.json()
        except requests.RequestException as err:
            raise Exception(
                "Problem with API.post..." + str(requests.RequestException)
            ) from err

    def post_blob(self, f):
        """Post file to DHIS2 and return created UID for that file

        :rtype: str
        """

        url = f"{self.url}/fileResources"
        with open(f, "rb") as fName:
            files = {"file": (f, fName, "application/x-sqlite3", {"Expires": "0"})}
            try:
                r = requests.post(url, files=files, auth=self.auth)
                if r.status_code not in (200, 202):
                    raise Exception(
                        "Problem with API.post_blob..."
                        + f"HTTP Code: {r.status_code}..."
                        + str(r.text)
                    )
                else:
                    response = r.json()
                    file_id = response["response"]["fileResource"]["id"]
                    return file_id
            except requests.RequestException as err:
                raise Exception(
                    "Problem with API.post_blob..." + str(requests.RequestException)
                ) from err


class VerbalAutopsyEvent:
    """Create DHIS2 event + a BLOB file resource

    :param va_id: UID for verbal autopsy record
      (used as a DHIS2 data element)
    :type va_id: string
    :param program: UID of the DHIS2's Verbal Autopsy program
    :type program: string
    :param dhis_orgunit: UID for the DHIS2 Organization Unit where the
      event (death) should be registered.
    :type dhis_orgunit: string
    :param event_date: Date of death with YYYY-MM-DD format
    :type event_date: datetime.date
    :param sex: Sex of the deceased (used as a DHIS2 data element).
      Possible values must fit to an option in the VA Program's "Sex"
      optionSet: female, male, missing, unknown).  If SmartVA is used
      to assign cause of death, then sex is an integer with 1 = male
      and 2 = female).
    :type sex: string or integer
    :param dob: Date of birth of the deceased with YYYY-MM-DD format
      (used as a DHIS2 data element)
    :type dob: datetime.date
    :param age: Age (in years) at time of death
    :type age: integer
    :param cod_code: Coded cause of death (must fit to an option in the
      VA Program's "CoD codes" optionSet.
    :type cod_code: string
    :param algorithm_metadata: Code for how the CoD was obtained (must
      fit in VA Program's "Algorithm Metadata" optionSet.
    :type algorithm_metadata: string
    :param odk_id: UID for the VA record assigned by the ODK Aggregate server
    :type odk_id: string
    :param file_id: UID for the blob file (containing the VA data and
      results) posted to (and assigned by) DHIS2 server.
    :type file_id: string
    """

    def __init__(
        self,
        va_id,
        program,
        dhis_orgunit,
        event_date,
        sex,
        dob,
        age,
        cod_code,
        algorithm_metadata,
        odk_id,
        file_id,
    ):
        self.va_id = va_id
        self.program = program
        self.dhis_orgunit = dhis_orgunit
        self.event_date = event_date
        self.sex = sex
        self.dob = datetime.datetime.strftime(dob, "%Y-%m-%d")
        self.age = age
        self.cod_code = cod_code
        self.algorithm_metadata = algorithm_metadata
        self.odk_id = odk_id

        if age != "MISSING":
            self.datavalues = [
                {"dataElement": "htm6PixLJNy", "value": self.va_id},
                {"dataElement": "hi7qRC4SMMk", "value": self.sex},
                {"dataElement": "mwSaVq64k7j", "value": self.dob},
                {"dataElement": "F4XGdOBvWww", "value": self.cod_code},
                {"dataElement": "wiJviUqN1io", "value": self.algorithm_metadata},
                {"dataElement": "oPAg4MA0880", "value": self.age},
                {"dataElement": "LwXZ2dZmJb0", "value": self.odk_id},
                {"dataElement": "XLHIBoLtjGt", "value": file_id},
            ]
        else:
            self.datavalues = [
                {"dataElement": "htm6PixLJNy", "value": self.va_id},
                {"dataElement": "hi7qRC4SMMk", "value": self.sex},
                {"dataElement": "mwSaVq64k7j", "value": self.dob},
                {"dataElement": "F4XGdOBvWww", "value": self.cod_code},
                {"dataElement": "wiJviUqN1io", "value": self.algorithm_metadata},
                {"dataElement": "LwXZ2dZmJb0", "value": self.odk_id},
                {"dataElement": "XLHIBoLtjGt", "value": file_id},
            ]

    def format_to_dhis2(self, dhisUser):
        """
        Format object to DHIS2 compatible event for DHIS2 API

        :param dhisUser: DHIS2 username for account posting the event
        :returns: DHIS2 event
        :rtype: dict
        """
        event = {
            "program": self.program,
            "orgUnit": self.dhis_orgunit,
            "eventDate": datetime.datetime.strftime(self.event_date, "%Y-%m-%d"),
            "status": "COMPLETED",
            "storedBy": dhisUser,
            "dataValues": self.datavalues,
        }
        return event

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__)


def create_db(fName, evaList):
    """
    Create a SQLite database with VA data + COD

    :param evaList: Event-Value-Attribute data structure with verbal autopsy
      data, cause of death result, and VA metadata.
    :type evaList: list
    :rtype: None
    """
    conn = sqlite3.connect(fName)
    with conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE vaRecord(ID INT, Attrtibute TEXT, Value TEXT)")
        cur.executemany("INSERT INTO vaRecord VALUES (?,?,?)", evaList)
    conn.close()


def getCODCode(myDict, searchFor):
    """Return COD label expected by (DHIS2) VA Program.

    :param searchFor: Cause of Death label returned by openVA.
    :type searchFor: string
    :rtype: str
    """
    for i in range(len(myDict.keys())):
        match = re.search(re.escape(searchFor), list(myDict.keys())[i])
        if match:
            return list(myDict.values())[i]


def findKeyValue(key, d):
    """
    Return a key's value in a nested dictionary.
    """
    if key in d:
        yield d[key]
    for k in d:
        if isinstance(d[k], list):
            for i in d[k]:
                yield from findKeyValue(key, i)


class DHIS:
    """Class for transfering VA records (with assigned CODs) to the DHIS2 server.

    This class includes methods for importing VA results (i.e. assigned causes of
    death from openVA or SmartVA) as CSV files, connecting to a DHIS2 server
    with the Verbal Autopsy Program, and posting the results to the DHIS2
    server and/or the local Transfer database.

    :param dhisArgs: Contains parameter values for connected to DHIS2, as
      returned by transferDB.configDHIS().
    :type dhisArgs: (named) tuple
    :param workingDirectory: Workind direcotry for the openVA Pipeline
    :type workingDirectory: string
    :raises: Exception
    """

    def __init__(self, dhisArgs, workingDirectory):
        self.dhisURL = dhisArgs[0].dhisURL
        self.dhisUser = dhisArgs[0].dhisUser
        self.dhisPassword = dhisArgs[0].dhisPassword
        self.dhisOrgUnit = dhisArgs[0].dhisOrgUnit
        self.dhisCODCodes = dhisArgs[1]
        self.dirDHIS = os.path.join(workingDirectory, "DHIS")
        self.dirOpenVA = os.path.join(workingDirectory, "OpenVAFiles")
        self.vaProgramUID = None
        self.nPostedRecords = 0

        dhisPath = os.path.join(workingDirectory, "DHIS")

        try:
            if not os.path.isdir(dhisPath):
                os.makedirs(dhisPath)
        except Exception as err:
            raise Exception("Unable to create directory" + dhisPath) from err

    def connect(self):
        """Setup connection to DHIS2 server.

        This creates a connection to DHIS2's VA Program ID
        by creating an instance of :class:`API <API>`.  This method
        also checks that the VA Program and the organization unit
        can both be found on the DHIS2 server.  The configuration
        settings for connecting to the DHIS2 (e.g., URL, username,
        password, etc.) are taken from the arguments passed to this
        method's class :class:`DHIS <DHIS>` (these settings can be
        created using the method
        :meth:`Pipeline.config <openva_pipeline.pipeline.Pipeline.config>`).

        :returns: A class instance for interacting with the DHIS2 API.
        :rtype: Instance of the :class:`API <API>` class
        """

        try:
            apiDHIS = API(self.dhisURL, self.dhisUser, self.dhisPassword)
        except requests.RequestException as e:
            raise Exception(str(e)) from e

        vaPrograms = apiDHIS.get(
            "programs", params={"filter": "name:like:Verbal Autopsy"}
        ).get("programs")
        if len(vaPrograms) == 0:
            raise Exception("No Verbal Autopsy Program found.")
        if len(vaPrograms) > 1:
            raise Exception("More than one Verbal Autopsy Program found.")
        self.vaProgramUID = vaPrograms[0].get("id")

        orgUnits = apiDHIS.get("organisationUnits").get("organisationUnits")
        validOrgUnit = self.dhisOrgUnit in [i["id"] for i in orgUnits]
        if not validOrgUnit:
            raise Exception("Did not find Organisation Unit.")
        return apiDHIS

    def postVA(self, apiDHIS):
        """Post VA records to DHIS.

        This method reads in a CSV file ("entityAttribuesValue.csv") with
        cause of death results (from openVA) then formats events and posts
        them to a VA Program (installed on DHIS2 server).

        :param apiDHIS: A class instance for interacting with the DHIS2 API
          created by the method :meth:`DHIS.connect <connect>`
        :type apiDHIS: Instance of the :class:`API <API>` class
        :returns: Log information receieved after posting events to the VA
          Program on a DHIS2 server (see :meth:`API.post <API.post>`).
        :rtype: dict
        :raises: Exception
        """

        evaPath = os.path.join(self.dirOpenVA, "entityAttributeValue.csv")
        if not os.path.isfile(evaPath):
            raise Exception("Missing: " + evaPath)
        recordStoragePath = os.path.join(self.dirOpenVA, "recordStorage.csv")
        if not os.path.isfile(evaPath):
            raise Exception("Missing: " + recordStoragePath)
        newStoragePath = os.path.join(self.dirOpenVA, "newStorage.csv")

        blobPath = os.path.join(self.dirDHIS, "blobs")
        try:
            if not os.path.isdir(blobPath):
                os.makedirs(blobPath)
        except Exception as err:
            raise Exception("Unable to create directory for DHIS blobs.") from err

        events = []
        export = {}

        dfDHIS = read_csv(evaPath)
        grouped = dfDHIS.groupby(["ID"])
        dfRecordStorage = read_csv(recordStoragePath)

        with open(newStoragePath, "w", newline="") as csvOut:
            writer = csv.writer(csvOut)

            header = list(dfRecordStorage)
            header.extend(["dhisVerbalAutopsyID", "pipelineOutcome"])
            writer.writerow(header)

            # this depends on openVA vs SmartVA
            for i in dfRecordStorage.itertuples(index=False):
                row = list(i)

                if row[5] != "MISSING" and row[5] is not None:
                    vaID = str(row[0])
                    blobFile = "{}.db".format(os.path.join(self.dirDHIS, "blobs", vaID))
                    blobRecord = grouped.get_group(str(row[0]))
                    blobEVA = blobRecord.values.tolist()

                    try:
                        create_db(blobFile, blobEVA)
                    except Exception as err:
                        raise Exception("Unable to create blob.") from err
                    try:
                        fileID = apiDHIS.post_blob(blobFile)
                    except requests.RequestException as e:
                        raise Exception(
                            "Unable to post blob to DHIS..." + str(e)
                        ) from e

                    algorithm = row[6].split("|")[0]
                    if algorithm == "SmartVA":
                        if row[1] in ["1", "1.0", 1, 1.0]:
                            sex = "male"
                        elif row[1] in ["2", "2.0", 2, 2.0]:
                            sex = "female"
                        elif row[1] in ["8", "8.0", 8, 8.0]:
                            sex = "don't know"
                        else:
                            sex = "refused to answer"
                    else:
                        sex = row[1].lower()
                    if isna(row[2]):
                        dob = datetime.date(9999, 9, 9)
                    else:
                        dobTemp = datetime.datetime.strptime(row[2], "%Y-%m-%d")
                        dob = datetime.date(dobTemp.year, dobTemp.month, dobTemp.day)
                    if isna(row[3]):
                        eventDate = datetime.date(9999, 9, 9)
                    else:
                        dod = datetime.datetime.strptime(row[3], "%Y-%m-%d")
                        eventDate = datetime.date(dod.year, dod.month, dod.day)
                    if isinstance(row[4], int):
                        age = row[4]
                    elif isinstance(row[4], float) and not isnan(row[4]):
                        age = int(row[4])
                    else:
                        age = "MISSING"
                    codCode = (
                        "99"
                        if row[5] == "Undetermined"
                        else getCODCode(self.dhisCODCodes, row[5])
                    )
                    algorithmMetadataCode = row[6]
                    odkID = row[7]

                    e = VerbalAutopsyEvent(
                        vaID,
                        self.vaProgramUID,
                        self.dhisOrgUnit,
                        eventDate,
                        sex,
                        dob,
                        age,
                        codCode,
                        algorithmMetadataCode,
                        odkID,
                        fileID,
                    )
                    events.append(e.format_to_dhis2(self.dhisUser))

                    row.extend([vaID, "Pushing to DHIS2"])
                    writer.writerow(row)
                else:
                    row.extend(["", "No CoD Assigned"])
                    writer.writerow(row)
        export["events"] = events
        try:
            log = apiDHIS.post("events", data=export)
        except requests.RequestException as e:
            raise Exception("Unable to post events to DHIS2..." + str(e)) from e
        self.nPostedRecords = len(log["response"]["importSummaries"])
        return log

    def verifyPost(self, postLog, apiDHIS):
        """Verify that VA records were posted to DHIS2 server.

        :param postLog: Log information retrieved after posting events to
          a VA Program on a DHIS2 server; this is the return object from
          :meth:`DHIS.postVA <postVA>`.
        :type postLog: dictionary
        :param apiDHIS: A class instance for interacting with the DHIS2 API
          created by the method :meth:`DHIS.connect <connect>`
        :type apiDHIS: Instance of the :class:`API <API>` class
        :raises: Exception
        """

        vaReferences = list(findKeyValue("reference", d=postLog["response"]))
        try:
            dfNewStorage = read_csv(self.dirOpenVA + "/newStorage.csv")
        except Exception as err:
            raise Exception(
                "Problem with DHIS.verifyPost...Can't find file "
                + self.dirOpenVA
                + "/newStorage.csv"
            ) from err
        try:
            for vaReference in vaReferences:
                postedDataValues = apiDHIS.get(f"events/{vaReference}").get(
                    "dataValues"
                )
                postedVAIDIndex = next(
                    (
                        index
                        for (index, d) in enumerate(postedDataValues)
                        if d["dataElement"] == "htm6PixLJNy"
                    ),
                    None,
                )
                postedVAID = postedDataValues[postedVAIDIndex]["value"]
                rowVAID = dfNewStorage["dhisVerbalAutopsyID"] == postedVAID
                dfNewStorage.loc[rowVAID, "pipelineOutcome"] = "Pushed to DHIS2"
            dfNewStorage.to_csv(self.dirOpenVA + "/newStorage.csv", index=False)
        except Exception as err:
            raise Exception(
                "Problem with DHIS.postVA...couldn't verify posted records."
            ) from err
