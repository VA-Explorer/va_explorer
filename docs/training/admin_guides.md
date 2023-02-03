# The Admin Role

## User Admin

As admin, you can create and manage user accounts. Each of these accounts will
have a role as described in User Roles and Capabilities (link). Additionally,
there are workflows available to you as an admin to affect users as a group or
as individuals described below.

### Loading Locations for Geographic Access Support

To set up VA Explorer for the Geographic Access mentioned in that section, you
must load location data into the system.

Locations in VA Explorer follow a hierarchical structure. A specific geographic
region or jurisdiction has a name ("Name"), a type ("Type"), and a parent
("Parent"). By specifying the Parent field, you can achieve the arbitrary level
of nesting required to make a tree.

The table below shows an example location hierarchy for States, Counties, and
Cities in the United States. In this example, we have one state (California), two
counties (Marin and Los Angeles), and three cities (Sausalito, San Rafael, and
Los Angeles).

```{csv-table} An example geographic hierarchy in tabular format
:header-rows: 1
Name,Type,Parent
California,State,
Marin County,County,California
Sausalito,City,Marin County
San Rafael,City,Marin County
Los Angeles County,County,California
Los Angeles,City,Los Angeles County
```

```{figure} ../_static/img/geo_hierarchy.png
:width: 75%

<small> A tree data structure showing the example geographic hierarchy from the previous table</small>
```

The input is similarly structured to support any number of geographic hierarchies
for VA Explorer users. An example of this in CSV form can be downloaded here
(external link). With a CSV file in hand, you can now supplement your initial
system set up with the `load_locations` management command. Full usage details
for this are provided in Management Commands (link).

Following this command, VA Explorer should support geographic restrictions to any
area or facility you’ve provide, making them available during user creation and
editing. Note that access to geographies higher up in the given tree equates to
access for that geographic area as well as all its children-geographies. For
example, in the above tree a user with access to California also has access to
Marin County, Los Angeles County, Sausalito, San Rafael, and Los Angeles.

### Creating & Editing Users

Click "Users" in the navigation bar to visit the Users page. Click the "Create
User" button to access the user creation form. Alternatively, click the "Edit"
button in the table row for the user you would like to edit. Required fields are
marked with an asterisk(*). To fill in the form:

1. Enter the user’s name

1. Enter the user’s email address. An email address can be used in the system once

1. Choose the user’s role from the dropdown menu

1. Check "Can View PII" if the user is allowed to view PII in the system. Also
check "Can Download Data" if the should be allowed to export VA data from the
system. See Abilities to Download and View PII Data (link) for details on these
permissions if needed

1. Select the geographic region(s), facility, facilities this user can access.
Users with a Field Worker role must be assigned to at least one facility

1. If user is a Field Worker, also enter their username if known. This field is
used to associate the field worker user with data imported from outside VA
Explorer (from locations such as ODK or from CSV file) and allow the field worker
to "own" their VAs

Click "Create" to create the user or "Update" if editing a user. "Cancel" will
take you back to the Users page without completing the action.

When the "Create" button is clicked during the "Create" process or the "Update"
button is clicked during the "Edit" process, VA Explorer validates the information
you have entered. If there are errors associated with the provided data, VA
Explorer will not create or update the user and the system will show error messages
in red underneath the fields that require correction. Follow instructions to
correct these errors and complete the user creation or edit process if needed.

### Deactivating Users

User accounts are deactivated rather than deleted from VA Explorer. When a user
account is deactivated, they will no longer be able to sign into the system.
Their associated data, however, will still be visible. To deactivate a user,
click "Users" in the navigation bar to visit the Users page. Click the "Edit"
button in the table row for the user you would like to deactivate. Uncheck the
"Active" checkbox. Click "Update." The user will now be deactivated.

### Bulk Creating Users

If you would like to create multiple users at once, particularly during initial
system set up, VA Explorer provides that functionality as a management command.
Please refer to Management Commands (link) for details on running
`get_user_form_template` and `bulk_load_users` to obtain a bulk user creation
template and to create your set of users based on that input file.

## Data Admin

As admin, you have full access to all data-related actions. Each step of the
process, from import to editing, to export has workflows available to you as an
admin to affect it as needed.

### Manually Importing Data

If you would like to manually import data from file, (perhaps if troubleshooting
the automatic import process) VA Explorer supports this through the `load_va_csv`
management command. Please refer to Management Commands (link) for details on
usage.

Similarly, if you have configured VA Explorer to integrate with ODK and would
like to manually import data from ODK, VA Explorer also supports this. Use
`import_from_odk` similarly detailed in Management Commands (link)

### Manually Running Coding Algorithms

VA Explorer currently supports the InterVA5 coding algorithm and its associated
settings to assign cause of death (COD) and may support other coding algorithms
in the future such as InSilicoVA. The InterVA5 coding algorithm depends on the
docker services as described in Algorithm Support (link)

To run InterVA5 manually, use `run_coding_algorithms` or see the entry for it in
Management Commands (link) for full usage details. After the command has finished
execution, a brief report of results should be printed to console used to run the
management command (ex. Coded 24 verbal autopsies (out of 30) [6 issues]) or an
error message if pyCrossVA or InterVA5 are somehow unavailable; if that is the
case, please refer to the Troubleshooting (link) section.

## Management Commands

Beyond actions supported by the VA Explorer interface, there are a series of
management commands available exclusively to developers, admins, and IT staff
helping to maintain the service. To take advantage of these special commands,
admins and IT staff need to, from the server hosting the VA Explorer instance,
enter VA Explorer’s main Django container like so
`docker exec -it va_explorer_django_1 bash`. From there `manage.py` is available
for calling the following commands via:

```shell
manage.py <command> --<parameter_name>=<parameter_input>
```

from within the container. Below is a selection of management commands,
generally useful to admins. An even fuller list of these can be found under
Development Commands (link)

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.50\linewidth-2\tabcolsep}|
.. flat-table:: Descriptions and lists of parameters for select management commands related to administration of VA Explorer
  :widths: 3 3 5
  :header-rows: 2

  * - :rspan:`1` Command Name
    - Parameter Names
    - :rspan:`1` Description

  * - ``(*)`` = Required

  * - :rspan:`1` ``load_va_csv``
    - ``--csv_file`` ``(*)``
    - :rspan:`1` Used to manually import data from file to into VA Explorer’s
      database. ``csv_file`` is a filename in the local folder or ``unix:path``
      format location of the file. Can be used with ``random_locations`` for
      test or demo data to randomly assign the VA to a field worker with
      specific location restrictions. ``True`` or ``False``; defaults to
      ``False``

  * - ``--random_locations``

  * - :rspan:`1` ``load_locations``
    - ``--csv_file`` (*)
    - :rspan:`1` Used to load initial location date data needed to support
      Geographic access. ``csv_file`` is a filename in the local folder or
      ``unix:path`` format location of the file. Can be used with
      ``delete_previous`` to delete existing location data and start fresh with
      the new locations being loaded. ``True`` or ``False``; defaults to
      ``False``

  * - ``--delete_previous``

  * - :rspan:`1` ``run_coding_algorithms``
    - ``--overwrite``
    - :rspan:`1` Used to call supported algorithms for assignment of cause of
      death to all VAs. ``overwrite`` allows this command to clear (and save)
      all existing CoD assignments before running. ``True`` or ``False``;
      defaults to ``False`` ``cod_fname`` is a filename or unix:path format
      location to save the old CoDs to. Defaults to ``old_cod_mapping.csv``

  * - ``--cod_fname``

  * - ``get_user_form
      _template``
    - ``--output_file``
    - Utility to obtain a bulk user creation template csv with header fields
      corresponding to fields of the current User model. ``output_file`` is a
      filename or ``unix:path`` format location to save template to. Default is
      ``user_form_fields.csv``

  * - :rspan:`1` ``bulk_load_users``
    - ``--user_list_file`` ``(*)``
    - :rspan:`1` Used to bulk create user accounts, assigning a temporary
      password to each. ``user_list_file`` is a filename in the local folder or
      ``unix:path`` format location of the users file. Can be used with
      ``email_confirmation`` if an email server has been setup to automatically
      send an email with the new temporary password to each created user.
      ``True`` or ``False``; defaults to ``False`` (prints to console instead so
      passwords must manually be passed to users somehow)

  * - ``--email_confirmation``
````

% Comment: We break the table here because the pdf rendering was flying off the page

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.50\linewidth-2\tabcolsep}|
.. flat-table::
  :widths: 3 3 5
  :header-rows: 0

  * - :rspan:`1` ``export_user_info``
    - ``--output_file``
    - :rspan:`1` Used to export an anonymized (No PII) list of all users in the
      system along with their roles and permissions. Useful for non-invasively
      correlating user activity in VA Explorer logs. ``output_file`` is a
      filename in the local folder or ``unix:path`` format location of the file
      to export user info to. Defaults to ``user_list.csv``. ``user_file`` is a
      separate filename in the local folder or ``unix:path`` format location of
      a ``.txt`` file containing emails (one per line) of specific users to
      export. Defaults to all users if no file.

  * - ``--user_file``

  * - :rspan:`1` ``link_fieldworkers
      _to_vas``
    - ``--emails``
    - :rspan:`1` Used to manually link a group of field workers to their VAs via
      ``Id10010`` on the VA and ``username`` on the User. Matches are persisted
      by setting the VA's ``username`` field to the matching field on User.
      ``emails`` is a comma separated\, no spaces\, string of emails that can be
      used to specify specific field workers to match. By default\, all field
      workers are considered for matching. ``match_threshold`` is also available
      to adjust desired match similarity (ranging from any [incorrect] match at
      0% to allowing full matches only at 100%). Default is 80%.

  * - ``--match_threshold``

  * - ``mark_vas_as
      _duplicate``
    - None
    - Used to manually run (or re-run if config is changed) duplicate checking
      within VA Explorer. Contains no parameters as behavior is determined by
      the configuration variable ``QUESTIONS_TO_AUTODETECT_DUPLICATES`` see
      Configuration & Deployment (link)
````

Additionally, if VA Explorer has been configured with integrations, the following
additional management commands are available. If the environment variables (see
Integrations (link)) that enable these integrations to work automatically are not
defined, consider all parameters required for these management commands.

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.30\linewidth-2\tabcolsep}|p{\dimexpr 0.20\linewidth-2\tabcolsep}|p{\dimexpr 0.50\linewidth-2\tabcolsep}|
.. flat-table:: Descriptions and lists of parameters for select management commands related to integrations
  :header-rows: 1
  :widths: 3 2 5

  * - Command Name
    - Parameter Names
    - Description

  * - :rspan:`5` ``import_from_odk``
    - ``--email``
    - :rspan:`5` Used to manually import VA data from ODK Central. Parameters
      are as described for the equivalent environment variables listed in
      Integrations > ODK Central (link)
  
  * - ``--password``
  * - ``--project_name``
  * - ``--project_id``
  * - ``--form_id``
  * - ``--form_name``

  * - ``load_dhis_cod_codes``
    - ``--csv_file``
    - Used to manually setup VA Explorer to report WHO CoD Codes in the format
      expected by DHIS2 and must be run before first export will succeed.
      ``csv_file`` is a filename in the local folder or ``unix:path`` format
      location of the csv file. csv file has the header
      ``codsource,codcode,codname,codid``

  * - :rspan:`3` ``run_dhis``
    - ``--dhis_user``
    - :rspan:`3` Used to manually export VA data to DHIS2. Parameters are as described for the equivalent environment variables listed in Integrations > DHIS2 (link)

  * - ``--dhis_pass``
  * - ``--dhis_url``
  * - ``--dhis_orgunit``
````
