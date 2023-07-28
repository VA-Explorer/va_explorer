# Integrations

VA Explorer supports integrations with a variety of services, some built-in,
some external, in order to facilitate the quick and efficient movement or
processing of {term}`VA`s. In this section you will find information on these
integrations as well as details on how to enable them in VA Explorer if needed.

- ODK Central
- KoboToolbox
- DHIS2
- Algorithm Support
  - pyCrossVA
  - InterVA5

## Networking

When integrating services with VA Explorer, operators should be aware of additional
networking configuration if multiple docker-compose services are run on the same server.

docker-compose creates all containers that are part of its compose file under a
default bridge network to allow intercommunication for that service. This setup
does not allow one set of docker-compose managed containers to talk to another
(VA Explorer -> ODK for example) by default.

To support this use case, operators can create an external bridge network and
connect it to the necessary containers like so:

```sh
docker network create <external network name>
docker network connect <external network name> va_explorer_django_1
docker network connect <external network name> <other service's container name>
```

VA Explorer provides some additional network configuration to enable use of this
external network via `.env` variables:

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.50\linewidth-2\tabcolsep}|
.. flat-table:: List of all configuration options when integrating with ODK Central, plus default values and descriptions for each
  :widths: 3 3 5
  :header-rows: 1
  :stub-columns: 1

  * - Variable Name
    - Default Value
    - Description

  * - ``USE_GATEWAY``
    - ``False``
    - ``True`` or ``False``. Used by VA Explorer determine if an external docker
      network should be used by integrations. Defaults to `False`.

  * - ``DOCKER_GATEWAY``
    - ``""``
    - An http scheme (``http://`` or ``https://``) followed by the IP address
      given by ``docker network inspect <external network name>`` command. Found
      as the ``IPAM.Config.Gateway`` property's value. Used by VA Explorer as an
      adaptor for HOST value of the service you wish to integrate with. Defaults
      to an empty string.
````

These `.env` variables should supplement the variables described below in whichever
service(s) you wish to integrate with.

## ODK Central

VA Explorer supports integration with {term}`ODK` Central to provide both manual and
automatic import of {term}`VA` questionnaire responses. You can read more about {term}`ODK`
Central via [its documentation](https://docs.getodk.org/central-intro/).

- To perform manual imports of {term}`ODK` Central data, please see
[Data Admin](../training/admin_guides.md#data-admin) in the Admin training guides.

- To configure VA Explorer for automatic import of {term}`VA`s, the relevant `.env`
variables are detailed below. Once properly set, run `docker-compose up -d` to
push the new configuration. {term}`ODK` integration features within VA Explorer should
now appear and function.

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.50\linewidth-2\tabcolsep}|
.. flat-table:: List of all configuration options when integrating with ODK Central, plus default values and descriptions for each
  :widths: 3 3 5
  :header-rows: 1
  :stub-columns: 1

  * - Variable Name
    - Default Value
    - Description

  * - ``ODK_HOST``
    - ``""``
    - ``ip:port`` or ``unix:path`` format location for the ODK Central instance
      to connect to. Defaults to an empty string for no connection.
      **Recommended to customize.**

  * - ``ODK_SSL_VERIFY``
    - ``True``
    - ``True`` or ``False``. Used by VA Explorer determine enforcement of valid
      ssl/https connections. Defaults to `True` for enforcement.

  * - ``ODK_PROJECT_ID``
    - ``2``
    - Value indicating the ID of the project in ODK Central that holds Verbal
      Autopsy forms or data. Typically, a number found in the url when viewing
      the project in ODK. Defaults to ``2`` (ex. ``/#/projects/2``)

  * - ``ODK_FORM_ID``
    - ``va_who_v1_5_3``
    - Value indicating the ID of the Verbal Autopsy form within the given
      project. Typically, found in the form list under the "ID and Version"
      column. Defaults to the ID of an example VA form.

  * - ``ODK_EMAIL``
    - ``user@example.com``
    - Value indicating the email of the account you wish to use to login to ODK
      Central. Defaults to an example email. **Recommended to customize.**

  * - ``ODK_PASSWORD``
    - ``""``
    - Value indicating the password for the provided email's account. Defaults
      to a blank string. **Recommended to customize.**
````

## KoboToolbox

VA Explorer supports integration with KoboToolbox as an alternative to ODK that also
allows for both manual and automatic import of {term}`VA` questionnaire responses.
You can read more about KoboToolbox via [its documentation](https://support.kobotoolbox.org/).

- To perform manual imports of KoboToolbox data, please see
[Data Admin](../training/admin_guides.md#data-admin) in the Admin training guides.

- To configure VA Explorer for automatic import of {term}`VA`s, the relevant `.env`
variables are detailed below. Once properly set, run `docker-compose up -d` to
push the new configuration. Kobo integration features within VA Explorer should
now appear and function.

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.50\linewidth-2\tabcolsep}|
.. flat-table:: List of all configuration options when integrating with KoboToolbox, plus default values and descriptions for each
  :widths: 3 3 5
  :header-rows: 1
  :stub-columns: 1

  * - Variable Name
    - Default Value
    - Description

  * - ``KOBO_HOST``
    - ``""``
    - ``ip:port`` or ``url`` format location for the KoboToolbox instance
      to connect to. Defaults to an empty string for no connection.
      **Recommended to customize.**

  * - ``KOBO_SSL_VERIFY``
    - ``True``
    - ``True`` or ``False``. Used by VA Explorer determine enforcement of valid
      ssl/https connections. Defaults to `True` for enforcement.

  * - ``KOBO_API_TOKEN``
    - ``""``
    - Value used to authenticate requests to the KoboToolbox API. A string of
      ~40 lowercase letters/numbers. Found for your user at ``KOBO_HOST/token``
      when logged in to the instance. Inherits your same permissions.
      Defaults to an empty string. **Recommended to customize.**

  * - ``KOBO_ASSET_ID``
    - ``""``
    - Value identifying the project used to collect Verbal Autopsies within
      KoboToolbox. Typically found in the url when viewing the project on the
      instance (Ex. ``{KOBO_HOST}/#/forms/uk8r5yolfuacxkjibsj7nw/summary``) 
      Defaults to an empty string. **Recommended to customize.**
````

## DHIS2

VA Explorer supports integration with {term}`DHIS2` to export {term}`VA`s that have been
processed and assigned causes of death along for potential further use. You can
read more about {term}`DHIS2` via their documentation. Details on configuring
{term}`DHIS2` for use with Verbal Autopsies metadata is also available via the
[DHIS2 VA program open-source project](https://github.com/verbal-autopsy-software/DHIS2_VA_program).

To configure VA Explorer for automatic export of {term}`VA`s, the relevant `.env`
variables are detailed below. Once properly set, run `docker-compose up -d` to
push the new configuration. {term}`DHIS2` integration features within VA Explorer should
now appear and function.

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.50\linewidth-2\tabcolsep}|
.. flat-table:: List of all configuration options when integrating with DHIS2, plus default values and descriptions for each
  :widths: 3 3 5
  :header-rows: 1
  :stub-columns: 1

  * - Variable Name
    - Default Value
    - Description

  * - ``DHIS_HOST``
    - ``""``
    - ``ip:port`` or ``unix:path`` format location for the DHIS2 instance to
      connect to. Defaults to an empty string for no connection.
      **Recommended to customize.**

  * - ``DHIS_SSL_VERIFY``
    - ``True``
    - ``True`` or ``False``. Used by VA Explorer determine enforcement of valid
      ssl/https connections. Defaults to ``True`` for enforcement.

  * - ``DHIS_ORGUNIT``
    - ``wEVB21sQaHu``
    - Value indicating the root Organization Unit UID within your DHIS2
      organizational hierarchy. Should be available using the DHIS2 API Query:
      ``/api/organizationUnits?level=1``. **Recommended to customize.**

  * - ``DHIS_USER``
    - ``admin``
    - Value indicating the username of the account you wish to use to login to
      DHIS2 Defaults to DHIS2's existing default username credential.
      **Recommended to customize.**

  * - ``DHIS_PASS``
    - ``district``
    - Value indicating the password for the provided username's account.
      Defaults to the default credentials for DHIS2's default admin account.
      **Recommended to customize.**
````

If you encounter any issues during integration, please reference the
[Troubleshooting](../training/troubleshooting) section.

## Algorithm Support

VA Explorer provides built-in support for cause of death assignment via the
InterVA5 computer coded VA ({term}`CCVA`) algorithm without additional configuration.
If you would like to change how these services are configured (including the
HIV or Malaria prevalence variables for InterVA5) or point to a custom service
instead, this section will help with that. As a future expansion, VA Explorer
may provide built-in support for additional {term}`CCVA` algorithms.

### pyCrossVA

pyCrossVA is provided as a built-in docker service to allow VA Explorer to
transform {term}`VA`s into input suitable for cause of death assignment algorithms. You
can read more about it via its project page.

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.50\linewidth-2\tabcolsep}|
.. flat-table:: List of all configuration options when interfacing with the pyCrossVA service, plus default values and descriptions for each
  :widths: 3 3 5
  :header-rows: 1
  :stub-columns: 1

  * - Variable Name
    - Default Value
    - Description

  * - ``PYCROSS_HOST``
    - ``http://pycrossva:80``
    - ``ip:port`` or ``unix:path`` format location for the pyCrossVA service
      used by VA Explorer to prepare VAs for algorithm input. Defaults to
      built-in pyCrossVA docker service.
````

### InterVA5

InterVA5 is provided as a built-in docker service to allow VA Explorer {term}`VA`s
to be processed for likely cause of death. You can read more about it via its
project page.

````{eval-rst}
.. tabularcolumns:: |p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.25\linewidth-2\tabcolsep}|p{\dimexpr 0.50\linewidth-2\tabcolsep}|
.. flat-table:: List of all configuration options when interfacing with the InterVA service, plus default values and descriptions for each
  :widths: 3 3 5
  :header-rows: 1
  :stub-columns: 1

  * - Variable Name
    - Default Value
    - Description

  * - ``INTERVA_HOST``
    - ``http://interva5:5002``
    - ``ip:port`` or ``unix:path`` format location for the InterVA service used
      by VA Explorer to assign causes of death. Defaults to built-in InterVA
      docker service.

  * - ``INTERVA_MALARIA``
    - ``l``
    - One of the enumerations "h" (high), "l" (low), or "v" (very low). Used to
      indicate the prevalence of Malaria within the population. Defaults to "l"
      for low.

  * - ``INTERVA_HIV``
    - ``v``
    - One of the enumerations "h" (high), "l" (low), or "v" (very low). Used to
      indicate the prevalence of HIV within the population. Defaults to "v" for
      very low.

  * - ``INTERVA_GROUPCODE``
    - ``False``
    - ``True`` or ``False``. Used to set whether the InterVA cause grouping code
      is included with cause of death output. Defaults to ``False``
````
