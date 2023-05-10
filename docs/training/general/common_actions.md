# Common Actions Across User Roles

## Signing in for the First Time

Signing into VA Explorer requires an email address and password. You will use a
temporary password obtained from either system-generated email or your
administrator when signing in for the first time. Contact your admin if you do
not have a temporary password or cannot find it.

1. Navigate to VA Explorer in your web browser. Compatible web browsers include
Google Chrome, Microsoft Edge, Mozilla Firefox, and Apple Safari.

1. Use your email address and your temporary password to sign in. You will be
prompted to choose a new password on the next page. Follow the instructions to
create a strong password that will help protect your VA Explorer account.

1. After signing in, the application will take you to the Home page. The Homepage
shows trends of {term}`VA`s collected and coded, as well as a snapshot of {term}`VA`s with
coding issues and {term}`VA`s coded with Indeterminate cause of death. The scope of {term}`VA`
data shown on the Home page depends on your assigned role and geographic access.

- **For Field Workers:** If you are assigned the Field Worker role, the Homepage
  shows trends and data on the {term}`VA`s for your location.
- **For All Other Roles:** For all other roles, data on the Home page are
  limited to the specific regions or facilities you can access.

## Viewing Your Account Profile

Your profile shows the role you have been assigned, your geographic access, and
actions you can take in VA Explorer, such as viewing {term}`PII` and downloading data.
These account settings are described in [User Roles and Capabilities](../user_guides.md)
To view your account profile:

1. Click your name in the upper right-hand corner of the navigation bar; a
dropdown menu will open.

1. Click the "My Profile" option within the dropdown menu.

Please contact your administrator if you need to update your account settings or
if something looks incorrect. Only individuals with administrator roles can
update user accounts.

## Changing Your Password

To change your password while signed into VA Explorer:

1. Click your name in the upper right-hand corner of the navigation bar; a
dropdown menu will open.

1. Click the "Change Password" option within the dropdown menu.

1. Enter your current password.

1. Choose a new password, following instructions to enter a valid password twice.

If you do not know your current password, sign out of VA Explorer and click
"Forgot Password?" You will be instructed to enter the e-mail address associated
with your account, and VA Explorer will send an email with a link allowing you
to reset it.

## Using the Analytics Dashboard

All users can view the {term}`VA` Analytics Dashboard to see information on the {term}`VA`s
(filtered to their level of permissions and access) that have successfully been
assigned a cause of death. To do so, click "Dashboard" in the navigation bar to
view it.

The {term}`VA` Analytics Dashboard is a dynamic, visualization-based dashboard that helps
you explore cause of death data. It has three global filters that simultaneously
update all graphs, maps, and statistics found in the top left of the dashboard
page and directly above the heatmap. The global filters include:

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.20\linewidth-2\tabcolsep}|p{\dimexpr 0.35\linewidth-2\tabcolsep}|p{\dimexpr 0.45\linewidth-2\tabcolsep}|
.. flat-table:: Specific descriptions and usage info for select filters available via the VA Explorer dashboard
  :widths: 2 4 5
  :header-rows: 1
  :stub-columns: 1

  * - Filter
    - Description
    - How to Use

  * - Death Date
    - View analytics for a specific date of death time frame
    - Choose the time frame you want to explore from the Time Period dropdown
      menu (ex. Within 1 Month, Within 1 Year, or Custom)

  * - Cause of Death
    - View analytics for a particular cause of death
    - Choose a cause of death or a category of causes (ex. Infectious, NCD,
      etc.) from the Causes dropdown menu

  * - Location
    - Filter analytics to specific location(s)
    - Choose specific geographic regions using the province/district selector
      and location dropdown or click a region on the map.
````

## Viewing Dashboard Components

The Dashboard includes several visualizations, including:

- A dynamic heatmap showing geographical trends, with ability to filter for
regions of interest. Found in the bottom left of the dashboard page.

- Cause of death plots. Found in the top right of the dashboard page.

- Death distributions by age, gender, and place of death ("demographics").
Found in the bottom right of the dashboard page.

- Cause of death trends over time. Found in the middle right of the dashboard page.

## Searching for and Reviewing Specific VAs

All roles have some level of access to search for and review specific {term}`VA`s. To do
so, click "Data Management" in the navigation bar to view the Data Management
page.

The Data Management page shows a paginated table of all the {term}`VA`s in the system
your account is eligible to see. For more information about your account and
eligibility, see [Viewing Your Account Profile](#viewing-your-account-profile).
On the Data Management page, you can search or filter available {term}`VA`s with the
following parameters:

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.3\linewidth-2\tabcolsep}|p{\dimexpr 0.7\linewidth-2\tabcolsep}|
.. flat-table:: Specific descriptions for each VA property available to filter with
  :widths: 3 7
  :header-rows: 1
  :stub-columns: 1

  * - Field
    - Description

  * - ID
    - The unique numeric identifier assigned to the specific VA in VA Explorer.

  * - Interviewed
    - The date the VA interview was conducted. If your account does not have PII access,
      you will see "Date Unknown".

  * - Facility
    - The facility where the VA was collected. If facility information is
      missing, you will see "Location Unknown".

  * - Deceased
    - The name of the deceased individual. If your account does not have PII
      access, you will see "Subject Unknown".

  * - Deathdate
    - The date of the individual’s death. If the VA is missing this information,
      you will see "Date Unknown".

  * - Cause
    - The cause of death assigned by coding algorithm. If the VA has not yet
      been coded, "Not Coded" will be displayed. A VA is "Not Coded" if the
      algorithm has not been run or if error(s) prevent the VA from being coded.

  * - Warnings
    - The count of warnings generated by the coding process. An example of a
      warning you might see for InterVA5 is: "field ageInYears2, age was not
      provided or not a number.

  * - Errors
    - The count of errors generated by the coding process. An example of an
      error you may see for InterVA is: "Error in age indicator: Not Specified."
````

In addition to searching and filtering, users may also have access to the
following actions depending on their permissions:

- Sort {term}`VA` table data by column value by clicking any of the column headers.
Clicking again reverses the sort order of the column

- Download {term}`VA` table data by clicking the "Export" button to be directed to the
Export page with your search parameters automatically filled into the export form.

- View {term}`VA` details by clicking the "View" button on any individual {term}`VA`. See
details below.

## Viewing Details for Individual VAs

When viewing a specific {term}`VA`, the resulting page may show a couple of tabs at the
top below the {term}`VA`s ID. Users with permission to change {term}`VA`s will also see the
option to repair the {term}`VA` via an "Edit Record" button. See
[Repairing VA Errors & Warnings](../user_guides.md#repairing-va-errors--warnings)
for details on editing {term}`VA`s. Quick navigation options to automatically scroll to
the top or bottom of the {term}`VA` responses is available via the floating action
button in the bottom right.

### Record

This tab is always visible and shows the {term}`VA` questionnaire data, including:

- The question ID corresponding to the {term}`WHO` standard instrument
- The text of question associate that pairs with each question ID
- The response or calculation for each question

By default, all empty fields are hidden so that only questions with answers are
shown. Revealing these is possible by unchecking the "Hide Empty Fields" box in
the top right of this tab.

### Coding Issues

This tab will become visible if the individual {term}`VA` has any warnings or errors
associated with it.

These warnings and errors can be applied during data import or, more often,
after processing the {term}`VA` for cause of death.

- **(Errors)** these are issues that either VA Explorer or a coding algorithm
has determined is severe enough to totally prevent {term}`CoD` assignment. They will
need to be corrected.

- **(User Warnings)** these are issues that should be addressed because they
potentially block {term}`CoD` assignment or the accuracy of the assigned {term}`CoD`
but are not quite as severe.

- **(Algorithm Warnings)** these are warnings specifically provided by the
algorithm after assigning a {term}`CoD` that indicate the assignment may not be accurate.
Fixing these increases the accuracy of {term}`CoD` assignment. This tab will be visible
if the individual {term}`VA` has been edited or updated in any way since its initial import.

### Change History

This history provides for transparency, record integrity, and protection from
misuse for {term}`VA`s and will take the form of an audit trail, a table of all changes,
with each row showing

- The date of the change
- The user who made the change
- The fields before and after the change

Additionally, this tab will contain two action buttons:

- **(Reset to Original)** To completely reset the {term}`VA` to the state it was in at
the time of original import. (Note that for this action, change history is still
preserved)

- **(Revert Most Recent Change)** To erase or undo the change described at the
top of the change history table (organized by most recent changes first)

```{admonition} Duplicate VAs
If your system is configured to automatically flag potential duplicate {term}`VA`s, you
may also see a yellow warning banner above these tabs. This banner alerts you
that VA Explorer has flagged this {term}`VA` as a possible duplicate. Please consult
with an administrator or data manager to determine any actions to take for
potential duplicate {term}`VA`s.
```
