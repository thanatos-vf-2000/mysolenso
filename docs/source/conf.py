# Sphinx configuration for automatic documentation of mysolenso
import os
import sys

# Make the package importable by Sphinx
sys.path.insert(0, os.path.abspath("../../src"))

# -- Project information ------------------------------------------------------
project = "mysolenso"
copyright = "2026, Franck VANHOUCKE"
author = "Franck VANHOUCKE"
release = "0.0.1a"

# -- Extensions ---------------------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",          # Generate docs from docstrings
    "sphinx.ext.autosummary",      # Automatic summary tables
    "sphinx.ext.napoleon",         # Google & NumPy docstring support
    "sphinx.ext.viewcode",         # Links to source code
    "sphinx.ext.intersphinx",      # Links to Python standard library docs
    "sphinx_autodoc_typehints",    # Types from Python annotations
]

# -- Autodoc configuration ----------------------------------------------------
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "private-members": False,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"
autosummary_generate = True

# -- Napoleon (Google style docstrings) configuration -------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_use_admonition_for_examples = True
napoleon_use_rtype = True

# -- Intersphinx --------------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),
}

# -- HTML output --------------------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
}
html_static_path = []
