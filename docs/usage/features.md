# Features

VA Explorer is an open-source web application built to help individuals and
organizations manage, analyze, and disseminate VAs while integrating with
existing CRVS systems at scale, simplifying the use of VAs for those individuals
and organizations. To that end, VA Explorer offers some major features:

- Tablet Friendly Interface
- User Identity & Access Management
- VA Data Import
- Data Collection Supervision
- Processing & Analyzing Cause of Death Data
- Repairing VA Errors
- VA Search & Retrieval
- Exporting Data

VA Explorer is in active development. A prototype, with the features described
here and screenshot with fake data, has been piloted in Zambia and is expected
to continue improving in response to new research and user feedback. If you
would like to see something specific from VA Explorer going forward, we look
forward to hearing from you! Please submit feedback, bug reports, feature
requests, etc. to our open-source project page.

For information on who should use VA Explorer, this documentation covers User
Training (link) for all user and support roles. Information on potential levels
of support that may be required to run a tool like VA Explorer is also available
via our IT Support Guides (link) training series.

## Tablet Friendly Interface

```{figure} ../_static/img/features/tablet_friendly.png
:alt: Picture of VA Explorer, comfortably visible on an iPad
:width: 50%

<small>Picture of VA Explorer, comfortably visible on an iPad</small>
```

VA Explorer needs to support users on desktops and mobile devices. This support
enables those whose roles place them in an office as well as those whose roles
take them out to fieldwork. To that end, VA Explorer’s interfaces are designed
to display comfortably at iPad resolution minimums (1024px x 768px) and scale
easily to larger devices.

## User Identity & Access Management

```{list-table}
:class: img-sidebyside
* - ```{figure} ../_static/img/features/user_iam_1.png
    :alt: VA Explorer's Users module, showing a list of users
    :width: 327.500
    :height: 247.719

    <small>Users module: A list of users</small>
    ```
  - ```{figure} ../_static/img/features/user_iam_2.png
    :alt: VA Explorer's Users module, showing an individual user edit form
    :width: 327.500
    :height: 247.719

    <small>Users module: An individual user edit form</small>
    ```
```

VA Explorer supports different user types and levels of access for those users
to facilitate roles-based VA workflows. This means VA Explorer offers features
like:

- Creation & management of user accounts by administrators
- Ability to disable, restrict access to data by feature, role assignment, or geography
- Ability for users to manage their own passwords automatically

## VA Data Import

```{list-table}
:class: img-sidebyside
* - ```{figure} ../_static/img/features/import_1.png
    :alt: VA Explorer's homepage, showing imported VAs & their statuses over time
    :width: 327.500
    :height: 247.719

    <small>Homepage charts showing imported VAs + statuses over time</small>
    ```
  - ```{figure} ../_static/img/features/import_2.png
    :alt: VA Explorer's Users module, showing an individual user edit form
    :width: 327.500
    :height: 247.719

    <small>Users module: An individual user edit form</small>
    ```
```

VA Explorer has limited functionality on its own – the true value of the tool
comes from how it helps you process your VA data. To obtain this data, VA
Explorer currently supports different data import methods (enumerated below).
After import, all VAs are searchable/ filterable via a number of useful
parameters such as interviewer, name of deceased, date, facility, cause of
death, and whether the VA has errors.

- **(Automatic) Click Import Data Button:** This format is the most user friendly:
the VA Explorer UI will detect whether you are using ODK or a more general CSV
import and react accordingly.

- **(Manual) Import from CSV:** This format allows the most flexibility: if your VAs
can be exported from their origin in CSV form, you can import them into VA
Explorer. See Admin Guides > Data Admin (link) training for specifics on how.

- **(Manual) Import from ODK:** This format implements manual support for ODK
integration: bring your VAs directly over from ODK like clicking the data import
button, but with more customization about how and when. See Admin Guides >
Data Admin (link) training for specifics on how.

## Data Collection Supervision

```{figure} ../_static/img/features/supervision.png
:alt: VA Explorer's Supervision module, showing an VA statistics grouped by facility
:width: 50%

<small>Supervision module: VA stats grouped by facility</small>
```

VA Explorer allows admins and data managers to supervise the origins of collected
VAs. Want to know which facilities are generating the most VA errors when
attempting to assign a COD? Want to know which interviewers/ field workers are
collecting the most VAs? This feature helps supervisor roles answer those types
of questions about the overall VA dataset.

- Overview of total VAs, total warnings/errors thrown during the CoD assignment,
and performance stats such as VAs/week

- Filter VAs under supervision by dates of interest

- Group data by interviewers/field workers or by facility for a different set of
insights

## Processing & Analyzing Cause of Death Data

```{list-table}
:class: img-sidebyside
* - ```{figure} ../_static/img/features/analysis_1.png
    :alt: VA Explorer's homepage, showing imported VAs & their statuses over time
    :width: 327.500
    :height: 247.719

    <small>Homepage charts showing imported VAs + statuses over time</small>
    ```
  - ```{figure} ../_static/img/features/analysis_2.png
    :alt: VA Explorer's Users module, showing an individual user edit form
    :width: 327.500
    :height: 247.719

    <small>Users module: An individual user edit form</small>
    ```
```

After importing VA data, one of VA Explorer’s key benefits is the ability to
quickly assign a CoD to each by running InterVA5. To enable this, VA Explorer
currently supports two ways to process VAs via CoD assignment, enumerated below.
The home page lists a quick reference of VAs that either contain coding errors
to be addressed or were assigned “Indeterminate” as the cause of death and may
require further investigation.

- **(Automatic) Click Run Coding Algorithms Button:** This format is the most user
friendly: the VA Explorer UI will detect all uncoded VAs and attempt to run
cause of death assignment on each or report any warnings/errors associated with
VAs that cannot receive CoD assignment.

- **(Manual) Run Coding Algorithms:** This format implements manual support for
InterVA5 integration: directly control the CoD assignment process for your VAs
via management command. See Admin Guides > Data Admin (link) training for
specifics on how.

Additionally, VA Explorer provides a dashboard of summary information,
analytics, and charts for VAs that have successfully assigned a cause of death.
The dashboard currently supports

- Showing an overview of VA processing progress with most recent dates and number
of coded compared to uncoded VAs

- Understanding geographical trends via a dynamic heat map, with zoom
capabilities to filter for regions of interest

- Showing cause of death plots for chosen regions

- Showing death distributions by age, gender, and place of death for chosen
regions

- Showing trends over time for chosen regions

- Ability to filter dashboard data by cause of death, dates of interest, and
geography

## Working with VA Questionnaires

```{list-table}
:class: img-sidebyside
* - ```{figure} ../_static/img/features/questionnaire_1.png
    :alt: Picture of an individual VA, showing responses
    :width: 327.500
    :height: 247.719

    <small>Record view showing VA responses.</small>
    ```
  - ```{figure} ../_static/img/features/questionnaire_2.png
    :alt: Picture of an individual VA, showing identified warnings
    :width: 327.500
    :height: 247.719

    <small>VA Issues tab, showing algorithm errors preventing coding</small>
    ```
```

Ideally the VAs collected by you, or your organization, are free of error. But
for occasions where they are not, VA Explorer supports troubleshooting and
correcting individual VA warnings or errors preventing cause of death assignment,
or those leading to an “Indeterminate” assignment by InterVA5.

- Field workers are able to view and edit VAs they collect
- Data Managers and Admins can do repairs for any VA they have access to
- View errors and warnings causing issues with VA from both VA Explorer and InterVA5 
- Easily edit VA answers with VA instrument compliant responses
- View change history and revert changes as needed for a VA

## Exporting Data

```{figure} ../_static/img/features/export.png
:alt: VA Explorer's Export module, showing an data export form
:width: 50%

<small>Export module: options form for data export</small>
```

Finally, when users would like to send the VAs processed by VA Explorer onto
another step in their analysis, or just save a copy for themselves, VA Explorer
supports data export in both CSV and JSON formats. Additionally, if VA Explorer
has been configured to integrate with DHIS2 then users can export their data
directly to that service. See DHIS2 (link) for more info.

- Choose between CSV and JSON data download
- Filter data downloaded to just the VAs of interest
- Optionally export direct to DHIS2 if your configuration supports it
