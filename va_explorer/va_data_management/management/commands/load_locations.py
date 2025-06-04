import argparse

import numpy as np
import pandas as pd
from anytree import LevelOrderIter, Node, RenderTree
from django.conf import settings
from django.core.management.base import BaseCommand

from va_explorer.va_data_management.models import Location

required_columns = ["province", "district", "key", "name", "status"]
missing_column_error_msg = ", ".join(required_columns)


class Command(BaseCommand):
    """
    Takes a list of locations with supporting metadata, converts it to a tree
    structure and then loads that tree into VA Explorer's database.

    Args:
        csv_file: File containing info on all facilities that are or ever have produced VAs.
            (See VA Spec choices tab for reference below and for their potential values)
            + Province - the label::English value of the lstprovince the location is within
            + District - the label::English value of the lstareas the location is within
            + Name - the label::English value for the lsthospital
            + Key - the choice name associated with the lsthospital
            + Status - whether the facility is still actively producing VAs

        --delete_previous (bool): If True, clears database first and inserts a
            new tree. If False (default), attempts to update existing Locations table
    """

    help = (
        "Loads initial location data into the database from a CSV file with"
        "relevant info. Required Columns: Province, District, Key, Name, Status."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=argparse.FileType("r"))
        parser.add_argument("--delete_previous", type=bool, nargs="?", default=False)

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        delete_previous = options["delete_previous"]

        tree = _treeify_facilities(csv_file)
        _process_facility_tree(tree, delete_previous=delete_previous)


def _process_csv(csv_file):
    try:
        df = pd.read_csv(csv_file, keep_default_na=False).rename(
            columns=lambda c: c.lower()
        )
    except FileNotFoundError:
        print(f"File '{csv_file}' not found.")
        exit(-1)

    if len(df.columns) < len(required_columns):
        print(
            f"Missing required columns ({missing_column_error_msg}). "
            + "Please ensure the provided CSV contains them."
        )
        exit(-1)
    elif set(df.columns) != set(required_columns):
        print(
            "CSV columns do not match the required format "
            + f"[{missing_column_error_msg}]."
        )
        exit(-1)

    # Do some post-processing. In this case turning human-readable 'Status'
    # into machine-readable is_active: <Bool>
    df = df.rename(columns={"status": "is_active"})
    df["is_active"] = df["is_active"].map({"Active": True, "Inactive": False})
    return df


def _has_child(parent, *args):
    """
    Helper method to check if a specific child exists under its parent.
    Check if all elements in args sequence exist as children.
    """
    current = parent
    for label in args[:-1]:
        found = False
        for child in current.children:
            if child.name == label:
                current = child
                found = True
                break
        if not found:
            return False
    # Check last item directly since there could be more siblings at lower levels.
    return any(child.name == args[-1] for child in current.children)


def _treeify_facilities(csv_file):
    """
    Converts csv_file input into a tree datastructure to validate readiness for
    database insertion.

    Tree has country root node and handles multiple facilities (leaf nodes) with
    the same name, as long as the path from the root to the leaf is unique for
    each name. For example:
        Zambia->Lusaka Province->Kafue District->Other Facility
        Zambia->Lusaka Province->Lusaka District->Other Facility are both valid.
        but adding a second
        Zambia->Lusaka Province->Lusaka District->Other Facility
        after the first would be a duplicate that is ignored.

    All nodes should contain name and location_type (one of 'province',
    'district', or 'facility' based on column name). Leaf nodes (facilities)
    contain additional info such as status and key.
    """
    df = _process_csv(csv_file)

    # TODO: turn this value into an env variable or make country requirement of csv
    root = Node("Zambia", location_type="country")
    node_lookup = {}
    for _, row in df.iterrows():
        province, district, _key, name, status = (
            row["province"],
            row["district"],
            row["key"],
            row["name"],
            row["is_active"],
        )

        # Create nodes along the way while checking uniqueness.
        p_node = None
        d_node = None
        f_node = None

        if province != "":
            province = f"{province} Province"
            if _has_child(root, province):
                p_node = node_lookup[(root.name, province)]
            else:
                p_node = Node(province, location_type="province", parent=root)
                node_lookup[(root.name, province)] = p_node

        if district != "" and p_node is not None:
            district = f"{district} District"
            if _has_child(p_node, district):
                d_node = node_lookup[(p_node.name, district)]
            else:
                d_node = Node(district, location_type="district", parent=p_node)
                node_lookup[(p_node.name, district)] = d_node
                node_lookup[(p_node.name, district)] = d_node

        if name != "" and d_node is not None:
            if _has_child(d_node, name):
                f_node = node_lookup[(d_node.name, name)]
                f_node = node_lookup[(d_node.name, name)]
            else:
                f_node = Node(name, location_type="facility", parent=d_node)
                node_lookup[(d_node.name, name)] = f_node

        # Add extra information only when reaching facility level.
        if f_node is not None:
            f_node.is_active = status
            f_node.key = _key

    if settings.DEBUG:
        for pre, _, node in RenderTree(root):
            print(f"{pre}{node.name}")

    return root


def _get_node_path(node):
    return "{}".format(
        node.separator.join([""] + [str(node.name) for node in node.path])
    )


def _process_facility_tree(tree, delete_previous=False):
    """
    Handle a given facility tree by processing each node to determine if they
    should be added to, removed from, or updated in the database.
    Report actions taken to the user at the end.
    """
    # Clear out existing locations if requested (typically for initialization only)
    if delete_previous:
        answer = input(
            "Loading a new location file with delete_previous=True may delete all of the VAs currently in the VAE database. By continuining, please make sure you have a backup of all data. Are you sure you want to continue?  yes/no "
        )
        if answer.upper() in ["Y", "YES"]:
            Location.objects.all().delete()

    # Only consider fields in both input and Location schema
    db_fields = {field.name for field in Location._meta.get_fields()}
    data_fields = set(vars(tree.leaves[0]).keys())
    common_fields = list(data_fields.intersection(db_fields))

    db = {location.path_string: location for location in Location.objects.all()}

    # Use anytree datastructure to insert or update database locations stored
    # as django-treebeard style models. Also track actions for reporting
    location_ct = update_ct = delete_ct = 0
    for node in LevelOrderIter(tree):
        model_data = {k: v for k, v in node.__dict__.items() if k in common_fields}
        model_data["path_string"] = path = _get_node_path(node)

        if node.parent:
            # first, check that parent exists. If not, skip location due to
            # integrity issues
            parent_node = db.get(_get_node_path(node.parent), None)
            if parent_node:
                # update parent to get latest state
                parent_node.refresh_from_db()
                # next, check for current node in db to update. If not, create new child.
                current_node = db.get(path)
                if current_node:
                    # update existing location fields with data from csv
                    old_values = {
                        k: v
                        for k, v in vars(current_node).items()
                        if k in common_fields
                    }
                    for field, value in model_data.items():
                        if value not in [np.nan, "", None]:
                            setattr(current_node, field, value)
                    new_values = {
                        k: v
                        for k, v in vars(current_node).items()
                        if k in common_fields
                    }
                    # only update if values changed
                    if old_values != new_values:
                        current_node.save()
                        update_ct += 1
                else:
                    db[path] = parent_node.add_child(**model_data)
                    location_ct += 1
            else:
                print(
                    f"Couldn't find location {node.name}'s "
                    + f"parent ({node.parent.name}) in system. Skipping.."
                )
        else:
            # add root node if it doesn't already exist
            if not db.get(path):
                print(f"Adding root node for {node.name}")
                db[path] = Location.add_root(**model_data)
                location_ct += 1

    # handle removals by checking if there are additional values in the db that
    # are not in the csv.
    paths = [_get_node_path(node) for node in tree.descendants] + [
        _get_node_path(tree.root),
        None,
    ]
    db_paths = list(
        Location.objects.all().only("path_string").values_list("path_string", flat=True)
    )
    extras = set(db_paths) - set(paths)
    if extras:
        for extra in extras:
            if str(extra).count("/") == 4:  ##i.e., if it is level 5 (hospital)
                node = db.get(extra)
                if node.is_active:
                    node.is_active = False
                    node.save()
                    delete_ct += 1

    # if non existent, add 'Null' location to database to account for VAs with
    # completely unknown locations
    if not Location.objects.filter(name="Unknown").exists():
        print("Adding NULL location to handle unknowns")
        Location.add_root(
            name="Unknown", key="other", location_type="facility", is_active=False
        )
        location_ct += 1

    print(f"  added {location_ct} new locations to system")
    print(f"  updated {update_ct} locations with new data")
    print(f"  marked {delete_ct} locations as inactive")
