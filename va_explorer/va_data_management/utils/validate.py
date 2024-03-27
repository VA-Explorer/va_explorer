from va_explorer.va_data_management.models import CauseCodingIssue
from va_explorer.va_data_management.utils.date_parsing import parse_date
from va_explorer.va_data_management.utils.location_assignment import assign_va_location


def validate_vas_for_dashboard(verbal_autopsies):
    # This validator is used to determine whether there is sufficient data to include
    # the record in the dashboard. Any errors or warnings are collected and reported
    # in the data manager.
    # The validation has to occur after the va's are created so we can reference
    # the va_id in the CauseCodingIssue.
    # The validator runs after va's are loaded and after a va is edited or reset.
    # TODO: would it be possible to move this to the VA model clean function?
    issues = []
    for va in verbal_autopsies:
        # clear all data related errors in case any were addressed
        CauseCodingIssue.objects.filter(verbalautopsy_id=va.id, algorithm="").delete()

        # Validate: date of death
        # Id10023 is required for the dashboard time frame filters
        # VA form guarantees this field is either "dk" or a valid datetime.date value
        try:
            va.Id10023 = parse_date(va.Id10023, strict=True)
        except:  # noqa E722 - Intent is to save to db, not do anything with exception
            issue_text = f"Error: field Id10023, couldn't parse date from {va.Id10023}"
            issue = CauseCodingIssue(
                verbalautopsy_id=va.id,
                text=issue_text,
                severity="error",
                algorithm="",
                settings="",
            )
            issues.append(issue)

        # Validate: ageInYears2
        # ageInYears2 is required for calculating mean age of death
        try:
            _ = int(float(va.ageInYears2))
        except:  # noqa E722 - Intent is to save to db, not do anything with exception
            issue_text = (
                "Warning: field ageInYears2, age was not provided or not a number."
            )
            issue = CauseCodingIssue(
                verbalautopsy_id=va.id,
                text=issue_text,
                severity="warning",
                algorithm="",
                settings="",
            )
            issues.append(issue)

        # Validate: age
        # age group can be determined from multiple fields, it's required for
        # filtering demographics
        if (
            va.isNeonatal != 1
            and va.isNeonatal != 1.0
            and va.isNeonatal != "1"
            and va.isNeonatal1 != 1
            and va.isNeonatal1 != 1.0
            and va.isNeonatal1 != "1"
            and va.isNeonatal2 != 1
            and va.isNeonatal2 != 1.0
            and va.isNeonatal2 != "1"
            and va.isChild != 1
            and va.isChild != 1.0
            and va.isChild != "1"
            and va.isChild1 != 1
            and va.isChild1 != 1.0
            and va.isChild1 != "1"
            and va.isChild2 != 1
            and va.isChild2 != 1.0
            and va.isChild2 != "1"
            and va.isAdult != 1
            and va.isAdult != 1.0
            and va.isAdult != "1"
            and va.isAdult1 != 1
            and va.isAdult1 != 1.0
            and va.isAdult1 != "1"
            and va.isAdult2 != 1
            and va.isAdult2 != 1.0
            and va.isAdult2 != "1"
        ):
            issue_text = "Warning: field age_group, no relevant data was found in \
                fields; isNeonatal, isNeonatal1, isNeonatal2, isChild, isChild1, \
                isChild2 isAdult, isAdult1, or isAdult2."
            issue = CauseCodingIssue(
                verbalautopsy_id=va.id,
                text=issue_text,
                severity="warning",
                algorithm="",
                settings="",
            )
            issues.append(issue)

        # Validate: location
        # location is used to display the record on the map
        if not va.location:
            # try re-assigning location using location logic described in loading.py
            va = assign_va_location(va)

            # if still no location, record an error
            if not va.location:
                issue_text = "ERROR: no location provided (or none detected)"
                issue = CauseCodingIssue(
                    verbalautopsy_id=va.id,
                    text=issue_text,
                    severity="error",
                    algorithm="",
                    settings="",
                )
                issues.append(issue)

        # if location is valid but inactive record a warning
        if (
            va.location
            and not va.location.is_active
            and va.location.name.casefold() != "unknown"
            and va.hospital.casefold() != "other"
        ):
            issue_text = "Warning: VA location was matched to facility known \
                to be inactive. Consider updating the location to an active \
                facility instead, or update the facility list."
            issue = CauseCodingIssue(
                verbalautopsy_id=va.id,
                text=issue_text,
                severity="warning",
                algorithm="",
                settings="",
            )
            issues.append(issue)

        # if location is "Other" (a valid, but non-informative location stemming
        # stemming from bad data) record a warning
        if (
            va.location
            and va.location.name.casefold() == "unknown"
            and va.hospital.casefold() == "other"
        ):
            issue_text = "Warning: location field (parsed from hospital) \
                was parsed as 'Other Facility'. May not fully show on \
                dashboards until underlying data is corrected to actual location."
            issue = CauseCodingIssue(
                verbalautopsy_id=va.id,
                text=issue_text,
                severity="warning",
                algorithm="",
                settings="",
            )
            issues.append(issue)

        # if location is "Unknown" (couldn't find match for provided location)
        # record a warning
        if (
            va.location
            and va.location.name.casefold() == "unknown"
            and va.hospital.casefold() != "other"
        ):
            issue_text = "ERROR: location field (parsed from hospital) did not \
                match any known facilities in the facility list. VA Explorer set \
                the location to 'Unknown.'  This VA will not show on \
                dashboards until underlying data is corrected to actual location."
            issue = CauseCodingIssue(
                verbalautopsy_id=va.id,
                text=issue_text,
                severity="error",
                algorithm="",
                settings="",
            )
            issues.append(issue)

    CauseCodingIssue.objects.bulk_create(issues)
