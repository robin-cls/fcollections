# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import pathlib

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'FCollections'
copyright = '2025, CNES'
author = 'CNES'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ['_templates']
exclude_patterns = []

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named "sphinx.ext.*") or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autodoc.typehints',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.mathjax',
    'sphinx.ext.napoleon',
    'sphinx_copybutton',
    'sphinx_tabs.tabs',
    'sphinx.ext.viewcode',
]

# -- Intersphinx ---------------------------------------------------------------
intersphinx_mapping = {
    'python': ('http://docs.python.org/3', None),
    'numpy': ('http://docs.scipy.org/doc/numpy/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
    'pyinterp': ('https://cnes.github.io/pangeo-pyinterp/', None),
    'xarray': ('https://docs.xarray.dev/en/stable/', None),
}

# -- Options for autosummary extension ---------------------------------------

autosummary_generate = True

# Import members that are declared in __init__.py
autosummary_imported_members = True
# If __all__ is defined document what is in __all__ and nothing else.
# If imported modules are in __all__ they are documented, whatever
# autosummary_imported_members.
autosummary_ignore_module_all = False

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_last_updated_fmt = '%a, %d %B %Y %H:%M:%S'

# Logo
html_logo = '_static/SWOT_spacecraft_model.png'

# Theme options
html_theme_options = {
    'logo_only': True,
    'navigation_depth': 4,
}

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    'css/custom.css',
]

sphinx_tabs_disable_tab_closing = True

import warnings

warnings.filterwarnings('ignore', category=UserWarning)
