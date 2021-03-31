import pandas
from simple_history.utils import bulk_create_with_history

from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.models import VerbalAutopsy
from va_explorer.va_data_management.models import CauseCodingIssue
from va_explorer.va_data_management.models import VaUsername


def validate_vas_for_dashboard(verbal_autopsies):
    # This validator is used to determine whether there is sufficient data to include
    # the record in the dashboard. Any errors or warnings are collected and reported
    # in the data manager.
    # The validation has to occur after the va's are created so we can reference the va_id in the CauseCodingIssue.
    # The validator runs after va's are loaded and after a va is edited or reset.
    # TODO: would it be possible to move this to the VA model clean function?
    issues = []
    for va in verbal_autopsies:
        # clear all data related errors in case any were addressed
        CauseCodingIssue.objects.filter(verbalautopsy_id=va.id, algorithm='').delete()
        
        # Validate: date of death
        # Id10023 is required for the dashboard time frame filters
        # the VA form guarantees this field is either "dk" or a valid datetime.date value
        if va.Id10023 == "dk":
            issue_text = "Error: field Id10023, date of death is unknown."
            severity = "error"
            issue = CauseCodingIssue(verbalautopsy_id=va.id, text=issue_text, severity=severity, algorithm='', settings='')
            issues.append(issue)
        
        # Validate: ageInYears
        # ageInYears is required for calculating mean age of death
        try:
            age = int(va.ageInYears)
        except:
            issue_text = "Warning: field ageInYears, age was not provided or not a number."
            severity = "warning"
            issue = CauseCodingIssue(verbalautopsy_id=va.id, text=issue_text, severity=severity, algorithm='', settings='')
            issues.append(issue)

        # Validate: age
        # age group can be determined from multiple fields, it's required for filtering demographics
        if va.age_group != "adult" and va.age_group != "neonate" and va.age_group != "child":
            if va.isNeonatal1 != 1 and va.isChild1 != 1 and va.isAdult1 != 1:
                try:
                    age = int(va.ageInYears)
                except:
                    issue_text = "Warning: field age_group, no relevant data was found in fields; age_group, isNeonatal1, isChild1, isAdult1, or ageInYears."
                    severity = "warning"
                    issue = CauseCodingIssue(verbalautopsy_id=va.id, text=issue_text, severity=severity, algorithm='', settings='')
                    issues.append(issue)

        # Validate: username
        # username associates the va record with a field worker
        username = va.username
        if username == "":
            issue_text = "Warning: field username, the va record does not have an assigned username."
            severity = "warning"
            issue = CauseCodingIssue(verbalautopsy_id=va.id, text=issue_text, severity=severity, algorithm='', settings='')
            issues.append(issue)
        else:
            va_user = VaUsername.objects.filter(va_username=username).first()
            if va_user is None:
                # TODO move this check to the VA clean function? and make username a drop down
                issue_text = "Warning: field username, the username provided is not a known Field Worker."
                severity = "warning"
                issue = CauseCodingIssue(verbalautopsy_id=va.id, text=issue_text, severity=severity, algorithm='', settings='')
                issues.append(issue)

        # Validate: location
        # location is used to display the record on the map
        # Id10058 may match a known facility, but if not we will user the interviewer's location as the default
        location = va.Id10058
        known_facility = Location.objects.filter(location_type='facility', name=location).first()
        if known_facility is None:
            issue_text = "Warning: field Id10058, the location provided was not a known facility. Using the username's facility as the default."
            severity = "warning"
            issue = CauseCodingIssue(verbalautopsy_id=va.id, text=issue_text, severity=severity, algorithm='', settings='')
            issues.append(issue) 
            va_user = VaUsername.objects.filter(va_username=username).first()
            if username == "" or va_user is None:
                # TODO move this check to the VA clean function? and make username a drop down
                issue_text = "Error: fields Id10058, username, cannot determine map location without field Id10058 or username."
                severity = "error"
                issue = CauseCodingIssue(verbalautopsy_id=va.id, text=issue_text, severity=severity, algorithm='', settings='')
                issues.append(issue)
            else:
                # TODO get the user's default location
                locations = va_user.user.location_restrictions
                if  locations.count() == 0:
                    issue_text = "Error: fields username, cannot determine map location, username has no assigned facilities."
                    severity = "error"
                    issue = CauseCodingIssue(verbalautopsy_id=va.id, text=issue_text, severity=severity, algorithm='', settings='')
                    issues.append(issue)  

    CauseCodingIssue.objects.bulk_create(issues)