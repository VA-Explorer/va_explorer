import pandas
from simple_history.utils import bulk_create_with_history

from va_explorer.va_data_management.models import VerbalAutopsy
from va_explorer.va_data_management.models import CauseCodingIssue

def validate_va_records(verbal_autopsies):
    # collect any errors
    # this has to occur after the va's are created because we need the va id for a foreign key
    # TODO break this out into a validation function so we can remove errors on updates
    issues = []
    for va in verbal_autopsies:
        # clear all data related errors
        CauseCodingIssue.objects.filter(verbalautopsy_id=va.id, algorithm='').delete()
        # update the validation for each va
        if va.Id10023 == "Unknown":
            issue_text = "Date of death is unknown."
            severity = "error"
            issue = CauseCodingIssue(verbalautopsy_id=va.id, text=issue_text, severity=severity, algorithm='', settings='')
            issues.append(issue)
        
        # validate age in years provided is a number, this is just a warning
        try:
            age = int(va.ageInYears)
        except:
            issue_text = "Missing required field: ageInYears was not provided or not a number."
            severity = "warning"
            issue = CauseCodingIssue(verbalautopsy_id=va.id, text=issue_text, severity=severity, algorithm='', settings='')
            issues.append(issue)

        # validate there is enough info to determine age group
        if va.age_group != "adult" and va.age_group != "neonate" and va.age_group != "child":
            if va.isNeonatal1 != 1 and va.isChild1 != 1 and va.isAdult1 != 1:
                try:
                    age = int(va.ageInYears)
                except:
                    issue_text = "Cannot determine age group. No data was found in any of the following fields; age_group, isNeonatal1, isChild1, isAdult1, or ageInYears."
                    severity = "warning"
                    issue = CauseCodingIssue(verbalautopsy_id=va.id, text=issue_text, severity=severity, algorithm='', settings='')
                    issues.append(issue)

    CauseCodingIssue.objects.bulk_create(issues)