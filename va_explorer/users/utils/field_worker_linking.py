import pandas as pd
from numpy import nan

from va_explorer.users.models import User
from va_explorer.va_data_management.models import VaUsername, VerbalAutopsy
from va_explorer.va_data_management.utils.location_assignment import fuzzy_match


# update field worker usernames by matching names against all known
# interviewer names from VAs
def link_fieldworkers_to_vas(emails=None, debug=False, match_threshold=80):
    user_objects = User.objects
    if emails:
        emails = [emails] if type(emails) is str else emails
        user_objects = user_objects.filter(email__in=emails)

    # if threshold is decimal, convert to percent
    if match_threshold > 0 and match_threshold < 1:
        match_threshold = int(100 * match_threshold)
    # get list of field worker user names (from Users)
    field_workers = filter(
        lambda x: x.is_fieldworker() and not x.name.startswith("Demo"),
        user_objects.all(),
    )
    name_to_user = {
        user.name.lower().replace(" ", "_"): user for user in list(field_workers)
    }

    # keep a list of va worker name keys for matching below
    va_worker_keys = get_va_worker_names()
    va_worker_names = list(va_worker_keys.keys())

    # convert va names to lowercase and replace underscores with spaces
    # fuzzy-match unique user_worker_names against unique va_worker_names
    user_names = list(name_to_user.keys())
    matches = [
        (
            user_name,
            fuzzy_match(
                user_name.lower(),
                None,
                options=va_worker_names,
                threshold=match_threshold,
            ),
        )
        for user_name in user_names
    ]
    # filter out tags that don't match any user names
    matches = list(filter(lambda x: x[1], matches))
    if debug:
        print(f"name to user: {name_to_user}")
        print(f"va worker names: {va_worker_names}")
        print(f"matches: {matches}")
    updated_va_ct = 0
    if len(matches) > 0:
        # update usernames of matching users
        name_dict = {user_name: va_user_name for user_name, va_user_name in matches}
        for name, new_username in name_dict.items():
            # update Username
            user = name_to_user[name]
            user.username = new_username
            # only set va username if current username doesn't match
            if new_username != user.get_va_username():
                user.set_va_username(new_username)
                # user.save()

            if debug:
                print(f"updating user {name}'s username to {new_username}")

            # Make sure all VAs with matching field worker name (Id10010) are
            # tagged with new username and get original field worker tag for
            # query (before it was lower-cased)
            va_worker_key = va_worker_keys[new_username]
            worker_vas = VerbalAutopsy.objects.filter(Id10010=va_worker_key)
            updated_va_ct += assign_va_usernames(
                worker_vas, [new_username], override=True
            )

        print(
            f"DONE. Updated {len(matches)} Field Worker Usernames and tagged \
            {updated_va_ct} VAs"
        )
        return matches
    else:
        print("failed to find any field worker tags that matched User names.")
        return None


# try to assign FieldWorker Usernames to a list of VAs if their field worker can
# be found in system. If no va list provided, will run on all vas in system.
def assign_va_usernames(
    vas=None, usernames=None, match_threshold=80, debug=False, override=False
):
    success_count = 0
    # if no usernames provided, match against all vausernames in system
    if not usernames:
        usernames = list(VaUsername.objects.values_list("va_username", flat=True))
    else:
        # if one username provided (as string), wrap in a list
        if type(usernames) is str:
            usernames = [usernames]
        # only keep provided usernames if they match a VAUsername in system
        usernames = list(
            VaUsername.objects.filter(va_username__in=usernames).values_list(
                "va_username", flat=True
            )
        )

    if not vas:
        vas = VerbalAutopsy.objects.all()

    tagged_users = set()
    if len(usernames) > 0:
        for va in vas:
            # if one username provided and override is true, skip matching and
            # override VA's username. Otherwise, only set va username if field
            # worker field matches a username in usernames.
            if len(usernames) == 1 and override:
                match = usernames[0]
            elif not pd.isna(va.Id10010):
                field_worker = va.Id10010
                match = fuzzy_match(
                    field_worker.lower(),
                    None,
                    options=usernames,
                    threshold=match_threshold,
                )
            if match:
                if debug:
                    print(f"Tagging va {va.id} with field worker {match}")
                va.username = match
                va.save()
                success_count += 1
                tagged_users.add(match)

        print(
            f"Successfully linked {success_count} VAs to {len(tagged_users)} \
            users ({tagged_users})"
        )
    else:
        print("WARNING: no field worker Usernames in system - failed to tag any VAs")
    return success_count


# get list of unique VA field worker names from VA records.
# return format: dictionary mapping lowercase names to raw names as they appear in VA
def get_va_worker_names(vas=None):
    if not vas:
        vas = VerbalAutopsy.objects
    # unique va field worker names (from field Id10010)
    va_worker_set = set(
        VerbalAutopsy.objects.filter(Id10010__isnull=False).values_list(
            "Id10010", flat=True
        )
    )
    # remove 'nan' and 'other' from the list
    va_worker_dict = {n.lower(): n for n in va_worker_set if n not in {"nan", "other"}}
    return va_worker_dict


# utility method to standardize a full name to lower-case first and
# last name separated by _
def normalize_name(name):
    final_name = None
    if name not in [None, "", nan]:
        names = name.strip().lower().replace(" ", "_").split("_")
        final_name = "_".join([names[0], names[-1]]) if len(names) > 1 else names[0]
    return final_name
