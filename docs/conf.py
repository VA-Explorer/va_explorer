# flake8: noqa
# allow svg/ raw html: https://pradyunsg.me/furo/customisation/footer/#using-embedded-svgs
import os
import sys

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
cwd = os.getcwd()
project_root = os.path.dirname(cwd)
sys.path.insert(0, project_root)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "VA Explorer Docs"
copyright = "2020-2023, MITRE Licensed under Apache 2.0"
author = "MITRE"

# The short X.Y version
version = "1.0"
# The full version, including alpha/beta/rc tags
release = "1.0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
# https://myst-parser.readthedocs.io/en/latest/index.html
# https://sphinx-toolbox.readthedocs.io/en/latest/index.html

extensions = [
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinx_design",
    "sphinx_copybutton",
    "linuxdoc.rstFlatTable",
    "sphinx_toolbox.latex.layout",
    "sphinx_toolbox.latex.toc",
]

templates_path = ["_templates"]
source_suffix = [".md"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
myst_heading_anchors = 3
myst_enable_extensions = [
    "html_admonition",
    "html_image",
    "replacements",
    "smartquotes",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# https://pygments.org/styles/

html_theme = "furo"
pygments_style = "tango"
pygments_dark_style = "one-dark"
html_title = project
html_theme_options = {
    "light_logo": "img/logo.png",
    "dark_logo": "img/logo_white.png",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/VA-Explorer/va_explorer",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
                </svg>
            """,
        },
    ],
}
today_fmt = "%Y-%m-%d"
numfig = False

html_static_path = ["_static"]
html_css_files = ["css/tweaks.css"]

# -- Options for PDF output --------------------------------------------------
# https://www.sphinx-doc.org/en/master/latex.html
# flat-table solution inspo: https://opensocdebug.readthedocs.io/en/latest/04_implementer/styleguides/docwriting.html#tables

latex_documents = [
    ("index", "VAExplorerDocs.tex", "VA Explorer Documentation", "MITRE", "manual"),
]

latex_elements = {
    "preamble": r"""
\let\cleardoublepage\clearpage
""",
}

latex_show_urls = "footnote"
latex_show_pagerefs = True
