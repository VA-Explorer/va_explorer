import re
from datetime import datetime

import numpy as np
import pandas as pd

from config.settings.base import DATE_FORMATS

DATE_FORMATS = DATE_FORMATS.keys()
NULL_STRINGS = ["nan", "dk"]


# helper method to parse dates in a variety of formats
def parse_date(date_str, formats=DATE_FORMATS, strict=False, return_format="%Y-%m-%d"):
    if type(date_str) is str:
        if len(date_str) == 0 or date_str.lower() in ["dk", "nan"]:
            return "dk"
        else:
            # try parsing using a variety of date formats
            for fmt in formats:
                try:
                    # remove any excessive decimals at end of string
                    date_str = date_str.split(".")[0]
                    return (
                        datetime.strptime(date_str, fmt).date().strftime(return_format)
                    )
                except ValueError:
                    pass
            # if we get here, all hardcoded patterns failed - try timestamp regex
            # if time time separator T present, strip out time and pull solely date
            if len(re.findall(r"\dT\d", date_str)) > 0:
                return re.split(r"T\d", date_str)[0]
            # if regex patterns not found, try pandas's to_datetime util as last resort
            else:
                try:
                    return pd.to_datetime(date_str).date().strftime(return_format)
                # Intent is only to handle exception with custom error or pass-through
                except:  # noqa E722
                    # if we get here, couldn't parse the date. If strict, raise error.
                    # Otherwise, return original string
                    if strict:
                        raise ValueError(
                            f"no valid date format found for date string {date_str}"
                        )
                    else:
                        return str(date_str)
    return "dk"


# vectorized method to extract dates from datetime strings
def to_dt(dates, utc=True):
    if type(dates) is list:
        dates = pd.Series(dates)
    return pd.to_datetime(
        pd.to_datetime(dates, errors="coerce", utc=utc).dt.date, errors="coerce"
    )


# get submissiondate for multiple vas (supports df, queryset or list of vas).
# First, checks for submissiondate. If empty, checks for va start date (Id10011).
# If empty, returns empty_string
def get_submissiondates(va_data, empty_string=None):
    # va_data is a dataframe - use vectorized logic
    if type(va_data) is pd.DataFrame:
        if not va_data.empty:
            assert "Id10011" in va_data.columns
            if "submissiondate" not in va_data.columns:
                return va_data["Id10011"]
            else:
                return np.where(
                    ~empty_dates(va_data, "submissiondate"),
                    va_data["submissiondate"],
                    va_data["Id10011"],
                )

    # va_data is list of va objects. Iterate through & get individual submission dates
    else:
        return [get_submissiondate(va, empty_string=empty_string) for va in va_data]


# get submissiondate for single va object. Uses the same field logic as above.
def get_submissiondate(va_data, empty_string=None, parse=False):
    if pd.isnull(va_data.submissiondate) or va_data.submissiondate in ["", "nan", "dk"]:
        if not pd.isnull(va_data.Id10011) and va_data.Id10011 not in ["", "nan", "dk"]:
            return parse_date(va_data.Id10011) if parse else va_data.Id10011
        else:
            return empty_string
    else:
        return parse_date(va_data.submissiondate) if parse else va_data.submissiondate


def empty_dates(va_df, date_col="submissiondate", null_strings=NULL_STRINGS):
    return (pd.isnull(va_df[date_col])) | (va_df[date_col].isin(null_strings))
