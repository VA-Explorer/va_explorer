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

        # Validate: ageInYears
        # ageInYears is required for calculating mean age of death
        try:
            _ = int(float(va.ageInYears))
        except:  # noqa E722 - Intent is to save to db, not do anything with exception
            issue_text = (
                "Warning: field ageInYears, age was not provided or not a number."
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
            va.age_group != "adult"
            and va.age_group != "neonate"
            and va.age_group != "child"
            and va.isNeonatal1 != 1
            and va.isChild1 != 1
            and va.isAdult1 != 1
        ):
            try:
                _ = int(float(va.ageInYears))
            except:  # noqa E722 - Intent is to save to db, not do anything with exception
                issue_text = "Warning: field age_group, no relevant data was found in \
                    fields; age_group, isNeonatal1, isChild1, isAdult1, or ageInYears."
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

        # if location is "Unknown" (couldn't find match for provided location)
        # record a warning
        if va.location and va.location.name == "Unknown":
            issue_text = "Warning: location field (parsed from hospital): provided \
                location was not a known facility. Set location to 'Unknown'"
            issue = CauseCodingIssue(
                verbalautopsy_id=va.id,
                text=issue_text,
                severity="warning",
                algorithm="",
                settings="",
            )
            issues.append(issue)

    CauseCodingIssue.objects.bulk_create(issues)
