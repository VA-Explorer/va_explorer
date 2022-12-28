# Integrations

VA Explorer supports integrations with a variety of services, some built-in,
some external, in order to facilitate the quick and efficient movement or
processing of VAs. In this section you will find information on these
integrations as well as details on how to enable them in VA Explorer if needed.

- ODK Central
- DHIS2
- Algorithm Support
  - pyCrossVA
  - InterVA5

## ODK Central

VA Explorer supports integration with ODK Central to provide both manual and
automatic import of VA questionnaire responses. You can read more about ODK
Central via its documentation.

- To perform manual imports of ODK Central data, please see Data Admin (link)
in the Admin training guides.

- To configure VA Explorer for automatic import of VAs, the relevant `.env`
variables are detailed below. Once properly set, run `docker-compose up -d` to
push the new configuration. ODK integration features within VA Explorer should
now appear and function.

```{csv-table}
:header-rows: 1
:stub-columns: 2
:escape: \
Variable Name,Default String,Description
`ODK_HOST`,`""`,`ip:port` or `unix:path` format location for the ODK Central instance to connect to. Defaults to an empty string for no connection. **Recommended to customize.**
`ODK_SSL_VERIFY`,`True`,`True` or `False`. Used by VA Explorer determine enforcement of valid ssl/https connections. Defaults to `True` for enforcement.
`ODK_PROJECT_ID`,`2`,Value indicating the ID of the project in ODK Central that holds Verbal Autopsy forms or data. Typically\, a number found in the url when viewing the project in ODK. Defaults to `2` (ex. `/#/projects/2`)
`ODK_FORM_ID`,`va_who_v1_5_3`,Value indicating the ID of the Verbal Autopsy form within the given project. Typically\, found in the form list under the "ID and Version" column. Defaults to the ID of an example VA form.
`ODK_EMAIL`,`user@example.com`,Value indicating the email of the account you wish to use to login to ODK Central. Defaults to an example email. **Recommended to customize.**
`ODK_PASSWORD`,`""`,Value indicating the password for the provided email's account. Defaults to a blank string. **Recommended to customize.**
```

If you encounter any issues during integration, please reference our
Troubleshooting (link) section.

## DHIS2

VA Explorer supports integration with DHIS2 to export VAs that have been
processed and assigned causes of death along for potential further use. You can
read more about DHIS2 via their documentation. Details on configuring DHIS2 for
use with Verbal Autopsies metadata is also available via the DHIS2 VA program
open-source project.

To configure VA Explorer for automatic export of VAs, the relevant `.env`
variables are detailed below. Once properly set, run `docker-compose up -d` to
push the new configuration. DHIS integration features within VA Explorer should
now appear and function.

```{csv-table}
:header-rows: 1
:stub-columns: 2
:escape: \
Variable Name,Default String,Description
`DHIS_HOST`,`""`,`ip:port` or `unix:path` format location for the DHIS2 instance to connect to. Defaults to an empty string for no connection. **Recommended to customize.**
`DHIS_SSL_VERIFY`,`True`,`True` or `False`. Used by VA Explorer determine enforcement of valid ssl/https connections. Defaults to `True` for enforcement.
`DHIS_ORGUNIT`,`wEVB21sQaHu`,Value indicating the root Organization Unit UID within your DHIS organizational hierarchy. Should be available using the DHIS API Query: `/api/organisationUnits?level=1`. **Recommended to customize.**
`DHIS_USER`,`admin`,Value indicating the username of the account you wish to use to login to DHIS. Defaults to DHIS2's existing default username credential. **Recommended to customize.**
`DHIS_PASS`,`district`,Value indicating the password for the provided username's account. Defaults to the default credentials for DHIS2's default admin account. **Recommended to customize.**
```

If you encounter any issues during integration, please reference our
Troubleshooting (link) section.

## Algorithm Support

VA Explorer provides built-in support for cause of death assignment via the
InterVA5 computer coded VA ({term}`CCVA`) algorithm without additional configuration.
If you would like to change how these services are configured (including the
HIV or Malaria prevalence variables for InterVA5) or point to a custom service
instead, this section will help with that. As a future expansion, VA Explorer
may provide built-in support for additional {term}`CCVA` algorithms.

### pyCrossVA

pyCrossVA is provided as a built-in docker service to allow VA Explorer to
transform VAs into input suitable for cause of death assignment algorithms. You
can read more about it via its project page.

```{csv-table}
:header-rows: 1
:stub-columns: 2
:escape: \
Variable Name,Default String,Description
`PYCROSS_HOST`,`http://pycrossva:80`,`ip:port` or `unix:path` format location for the pyCrossVA service used by VA Explorer to prepare VAs for algorithm input. Defaults to built-in pyCrossVA docker service.
```

### InterVA5

InterVA5 is provided as a built-in docker service to allow VA Explorer VAs to be
processed for likely cause of death. You can read more about it via its project
page.

```{csv-table}
:header-rows: 1
:stub-columns: 2
:escape: \
Variable Name,Default String,Description
`INTERVA_HOST`,`http://interva5:5002`,`ip:port` or `unix:path` format location for the InterVA service used by VA Explorer to assign causes of death. Defaults to built-in InterVA docker service.
`INTERVA_MALARIA`,`l`,One of the enumerations "h" (high)\, "l" (low)\, or "v" (very low). Used to indicate the prevalence of Malaria within the population. Defaults to "l" for low.
`INTERVA_HIV`,`v`,One of the enumerations "h" (high)\, "l" (low)\, or "v" (very low). Used to indicate the prevalence of HIV within the population. Defaults to "v" for very low.
`INTERVA_GROUPCODE`,`False`,`True` or `False`. Used to set whether the InterVA cause grouping code is included with cause of death output. Defaults to `False`
```
