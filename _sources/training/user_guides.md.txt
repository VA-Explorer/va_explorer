# User Roles

In addition to the training previously detailed for [Common Actions](general/common_actions),
users may want to read training specific to their role. This section offers guidance
for Data Managers, Data Viewers, and Field Workers. For Admins, please see the
next section [Admin Guides](admin_guides) which covers your more expansive abilities.

## Data Managers

As mentioned, Data Managers have near full access VA Explorer, equivalent to
admin access without the ability to create and manage user accounts. They should
support the admin in VA Explorer operations to reduce burden on Admins, who can
then focus on ensuring Data Managers have the users they need (such as Data
Viewers and Field Workers) to be effective. These guides help cover those tasks
Data Managers can undertake.

### Viewing Users & Supervision Information

As a Data Manager, you have access to the profiles of all VA Explorer users, but
do not have the ability to make changes to them, such as adding permissions. This
ability may be useful in determining if users you supervise have the correct
access, or facilities you supervise have the right amount of coverage through
user geographic access. To view the list of Users, click "Users" in the top
navigation bar. To view an individual user, click the "Show" button next to
their name.

Next, to view VA Explorer’s supervision information click "Supervision" in the
navigation bar to visit the Supervision page. This page shows {term}`VA`s collected in
the system grouped by Interviewer/ Field Worker or by Facility. In each case,
the page lists the following information to help you answer various supervision
questions such as:

- Which interviewer or facility is generating the most issues when we attempt to code {term}`VA`s?
  - Total Warnings
  - Total Errors
- Which interviewers or facilities are providing the most data and how often?
  - VAs / week
    - Total VAs
    - Total Weeks of Data
  - Date of Last Interview

When viewing data grouped by Interviewer/ Field Worker, this information (each
sub-bullet beneath the questions) is available for each individual Field Worker
(ex. Total {term}`VA`s collected by interviewer John Smith, total for …, etc.) and shows
the Facility that Field Worker is assigned to. However, when viewing data grouped
by Facility, the names of individual Interviewers/ Field Workers go away as the
information becomes summarized at the Facility level (e.g., John Doe and Jane
Roe each collected 20 {term}`VA`s for Example Clinic so Total {term}`VA`s now shows Example
Clinic – 40 total {term}`VA`s). Changing this grouping is done by toggling the "Group by"
dropdown in the top form and clicking "Go"

Additionally, it is possible to filter the supervision data in case you’d like
to see it for specific facilities or for certain date ranges (How many {term}`VA`s did
John Doe collect last month?). To apply a filter, enter in your parameters to
the form at the top and click the "Go" button.

### Exporting Data

Click "Export", either in the navigation bar, search interface, or the dashboard
to navigate to the Export page. When exporting data from VA Explorer for local use:

1. Either customize the data you would like to export by using the available
filters or confirm that the form has been auto-filled with the filters you were
using when navigating here from the search interface or dashboard. By default,
if no filters are applied, the system will attempt to export all the data you
have permissions to access.

1. Choose the export format: {term}`CSV` or {term}`JSON`.

1. Click "Download." A modal will appear explaining that your download is being
prepared and compressed to a .zip file. For the download to complete, do not
navigate away from the Export page. The modal will close automatically when the
download has finished. Please note that large file sizes may take a while to download.

### Running Data Cleanup Operations

VA Explorer can autodetect {term}`VA`s that are possible duplicates. The system flags
{term}`VA`s that match across a set of fields and shows these possible duplicates under
the "Data Cleanup" navigation bar item. The Data Cleanup functionality is
available when your system has been configured to autodetect potential duplicate
{term}`VA`s. By default, this feature is turned off. If you do not see the Data Cleanup
menu item and think you should, contact your system administrator for more
information.

As an example of how this feature works, let’s say your system is configured to
identify {term}`VA`s as duplicates if they match interview date, name, gender, and age
of the deceased person. When VA Explorer detects two (or more) {term}`VA`s that match
across these fields, it leaves the oldest one unmarked and flags all others as
possible duplicates.

The set of fields used to identify duplicates is configurable, and your system
administrator may set and update them.

To manage what is done with these {term}`VA`s flagged as potential duplicates, you may
delete them or edit the possible duplicate {term}`VA`s to remove them from detection.
See the table below for all actions you can take on the data cleanup page.

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.3\linewidth-2\tabcolsep}|p{\dimexpr 0.7\linewidth-2\tabcolsep}|
.. flat-table:: List of actions available through the data cleanup UI and what they accomplish
  :widths: 3 7
  :header-rows: 1
  :stub-columns: 1

  * - Action
    - Description

  * - Download All
    - Download all potential duplicate verbal autopsies to a CSV file for examination.

  * - Delete All
    - Delete all potential duplicate verbal autopsies. The oldest VA (by created timestamp)
      amongst a set of matching VA s is designated as the non-duplicate and kept
      in the system.

  * - View
    - View a single VA flagged as a possible duplicate.

  * - Download Individual
    - Download an individual verbal autopsy and verbal autopsy(ies) flagged as
      its potential duplicate(s) to a CSV file for examination.

  * - Delete Individual
    - Delete an individual VA from the system.

  * - View question list
    - View the list of questions used by your system to autodetect duplicates.
````

For further information relating to the identification of duplicates, please
either ask your admin, consult [Configuration & Deployment](../usage/getting_started/config)
for info on setting up or changing questions used for this process, or
[Management Commands](admin_guides.md#management-commands) for admin guidance on
running the process manually.

### Repairing VA Errors & Warnings

Occasionally, you may need to edit an individual {term}`VA`, especially in cases where
warnings or errors have been reported for the record. You can reach the Edit
form from the Individual {term}`VA` page by clicking the "Edit Record" button. Doing so
transforms the {term}`VA` responses into a series of form elements that are compliant to
the {term}`WHO` {term}`VA` instrument standard and make data entry for specifically formatted
values (such as datetime) easier. Questions that have already been answered will
be pre-filled with their responses. You can expect to encounter the following
types of form elements when editing the various responses to a {term}`VA`:

- **(Text Field)** For short responses
- **(Large Text Field)** For longer/ narrative-style responses
- **(Upload Selector)** For images and file attachments
- **(Datetime Selector)** For choosing a date and time response
- **(Radio Buttons)** For choosing 1 response from N (small #) choices
- **(Dropdown)** For choosing 1 response from N (large #) choices
- **(Calculated)** You are unable to edit these, they update according to other editable fields
- **(Checkboxes)** For selecting multiple responses to the same question

Using this form, you may edit the {term}`VA` as needed. Upon finishing, scroll or
navigate via the bottom right floating action button to the bottom of the page
and click "Save" to confirm your edits.

After editing a {term}`VA`, the natural next step is to see if the changes have corrected
any reported warnings or errors associated with the {term}`VA`. Data Managers can complete
this second step in the repair process by clicking "Home" in the navigation bar
to visit the Home page and starting a {term}`VA` coding job to assign Cause of Death:

- Click the "Run Coding Algorithms" button to execute the coding algorithm in
the background

If you receive any error messages following this, either reach out to your admin
or see our [Troubleshooting](troubleshooting.md) section

## Data Viewers

Data viewers have the simplest set of permissions, enabling them to view data
scoped to whichever restrictions their admins set. As a data viewer, VA Explorer
does not currently support any features unique to your role. Please consult the
[Common Actions](general/common_actions) section, particularly the Dashboard and
{term}`VA` Search interface guides for more info on available actions.

## Field Workers

Field Workers are similar to Data Viewers. However, they only see {term}`VA`s for their 
own location and can partially repair {term}`VA` Errors & Warnings for those {term}`VA`s. For a 
full listing of these, see [Common Actions](general/common_actions) or see below
for an explanation  of the "partial repair" workflow.

### Partially Repairing VA Errors & Warnings

As a Field Worker, you have the ability to make corrections to {term}`VA`s for your own 
location as a way of assisting Data Managers with the correction of any warnings 
or errors reported by VA Explorer. See [Repairing VA Errors & Warnings](#repairing-va-errors--warnings)
for details. However, you will not be able to create any {term}`VA` coding jobs to re-run 
cause of death assignment. Please reach out to the appropriate Data Manager or 
Admin to do this for you.

