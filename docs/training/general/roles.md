# User Permissions

There are four VA Explorer user roles, each with different capabilities. A user
may only have one role per account/email address, but there may be multiple
users assigned to each type of role (e.g., a user can only be one of Admin, Data
Manager, Data Viewer, or Field Worker; but there may be multiple Admins, Data
Managers, Data Viewers, and/or Field Workers). The table below provides a
high-level description of each role.

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.20\linewidth-2\tabcolsep}|p{\dimexpr 0.80\linewidth-2\tabcolsep}|
.. flat-table:: List of available roles and their descriptions
  :widths: 2 8
  :header-rows: 1
  :stub-columns: 1

  * - Role
    - Description

  * - Admin
    - Admins oversee the VA Explorer system. By default, Admins have full access
      to the application. This includes data for all VAs as well access to all
      system functions such as managing accounts, importing, processing, and
      exporting data.

  * - Data Manager
    - Data Managers have near full access VA Explorer, equivalent to admin
      access without the ability to create and manage user accounts. Has full
      access to VA data and system functions unless any restrictions
      (ex. Geographic) are placed on them by the admin.

  * - Data Viewer
    - Data Viewers have access that allows them use VA Explorer for reporting
      purposes – a Data Viewer can view, analyze via the dashboard, or search
      through VAs but cannot modify any VAs

  * - Field Worker
    - Field Workers have similar permissions to Data Viewers, but are allowed
      only allowed full access to view and modify VAs for their own location. 
      This allows them to assist data managers in repairing any cause of death 
      errors.
````

Users should have a role with the fewest capabilities and least record access
required to perform their job. For example, if a user only needs to be able to
view {term}`VA` data, a Data Manager role would not be appropriate.

## Geographic Access

Your admin may also associate your account with specific geographic regions or
facilities. This assignment is called "Geographic Access" in VA Explorer. If
your account has this restriction, VA Explorer only shows you {term}`VA`s from your
assigned regions or facilities. The default geographic restriction is the broadest
"National" access, which shows {term}`VA`s from all regions. To support additional
location restriction options beyond the default, Admins should follow the guide
in [Loading Locations for Geographic Access Support](../admin_guides.md#loading-locations-for-geographic-access-support)

## Abilities to Download and View PII Data

Personally Identifiable Information ({term}`PII`) is a category of information that can
be used to identify an individual. Some users may be further restricted from
viewing or downloading certain data such as {term}`PII` or, separately, from downloading
data altogether for privacy or policy reasons. Users do not have these restrictions
by default, so Admins will determine if individual users have this restriction.
If users have the download data restriction, they will not be able to use the
Export feature. If users are restricted from viewing {term}`PII`, the following fields
will not appear in the application or in downloaded data. Instead, fields will
automatically be replaced with `** redacted **`.

```{csv-table} List of VA fields redacted for users without PII viewing permissions
:header-rows: 1
:stub-columns: 1
:escape: \
VA Field,Meaning/Information Protected
"Id10007",Name of VA respondent
"Id10017",First name of subject
"Id10018",Surname of subject
"Id10061",Name of subject's father
"Id10062",Name of subject's mother
"Id10070",Subject death registration number
"Id10073",Subject national identification number
```
