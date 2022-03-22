import pandas as pd

from va_explorer.va_data_management.models import Location
from va_explorer.va_data_management.utils.location_assignment import fuzzy_match

# Get all relevant location ids (including descendants) for filtering.
# loc_query is a comma-separated list of either location ids or location names. If location names,
# perform name-based matching against all known locations in database.


# returns a list of location IDs matching location query.
def get_loc_ids_for_filter(loc_query):
    locs = loc_query.split(",")
    # first, assume locations are given as ids. If not, treat as names and perform name-based matching.
    try:
        loc_ids = [int(loc) for loc in locs]
        match_list = []
        for loc_id in loc_ids:
            # make sure location id is valid. Only proceed it matching location found
            loc_obj = Location.objects.filter(pk=loc_id).first()
            if loc_obj:
                match_list.append(loc_id)
                # add location descendants to match list
                match_list += list(
                    loc_obj.get_descendants().values_list("id", flat=True)
                )
    except:  # noqa E722 - Intent is to simply handle invalid location case
        # check query against all locations in db. If a match, get all location descendants if not already facility
        loc_df = pd.DataFrame(Location.objects.values("id", "name", "location_type"))
        for loc in locs:
            # perform name-based matching
            res = fuzzy_match(loc.lower(), loc_df, return_str=False)
            if res:
                if "id" in res:
                    match = Location.objects.get(pk=res["id"])
                else:
                    match = Location.objects.get(name=res["name"])

                # get descendants
                descendants = match.get_descendants().values_list("id", flat=True)
                match_list = [match.id] + list(descendants)
    return match_list
