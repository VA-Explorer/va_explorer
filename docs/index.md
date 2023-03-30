# VA Explorer: A Full Service VA Management Prototype

```{figure} _static/img/va_interview.jpg
:alt: Two women talking as one takes notes on a laptop
:width: 50%
:figclass: "none"
<small>An example VA Interview <br/> Image from 
healthdata.org/data-tools-practices/verbal-autopsy</small>
```

Verbal autopsies ({term}`VA`s) are a World Health Organization ({term}`WHO`) -standardized tool
for conducting structured interviews to determine an individual's most likely
cause of death ({term}`CoD`). {term}`VA`s use information from next of kin, or witnesses,
regarding symptoms and health history of the deceased prior to their death.

VA Explorer is an open-source web application built to help individuals and
organizations support the management, analysis, and dissemination of {term}`VA`s.
VA Explorer aims to support integration with existing civil registration and
vital statistics ({term}`CRVS`) systems at scale while simplifying the use of
{term}`VA`s for those individuals and organizations.

This documentation aims to be a universal reference for everything related to
VA Explorer. For example:

- If you are interested in using VA Explorer immediately, [Getting Started](usage/getting_started/index)
walks users through installing and running the service.

- For evaluating whether VA Explorer meets your or your organization’s needs,
more information on supported features can be found in [Features](usage/features) while
more info on the {term}`CRVS` systems VA Explorer works with can be found in [Integrations](usage/integrations)

- Those running an instance of VA Explorer already who would like to become more
familiar with what they can do in their system role as an Admin, Data Manager,
Data Viewer, or Field Worker can do so in [User Training](training/user_guides) or [Admin Training](training/admin_guides)

- Users wishing to report bugs, request features, or developers wishing to
contribute to the VA Explorer effort can find resources in [Development](develop)

**Contents:**

```{toctree}
---
maxdepth: 3
caption: Usage
---

usage/getting_started/index
usage/features
usage/integrations
```

```{toctree}
---
maxdepth: 3
caption: Guides
---

training/general/index
training/user_guides
training/admin_guides
training/it_guides
training/troubleshooting
```

```{toctree}
---
caption: Development
---

develop
```

% Comment: For below link: Assume deploy will upload a VAExplorerDocs.pdf to _static/ (CASE Sensitive)

```{toctree}
---
hidden:
caption: Additional Info
---

reference
Offline Docs <https://va-explorer.github.io/va_explorer/_static/VAExplorerDocs.pdf>
```

---

> Last Updated: {sub-ref}`today`
