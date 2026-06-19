"""Sphinx configuration for the Phone Management Application."""

import os
import sys

# Ensure src/ is importable for autodoc.
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("../src"))

project = "Phone Management Application"
author = "Nick Reese"
copyright = "2026, Nick Reese"
version = "0.1"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

master_doc = "index"
html_theme = "alabaster"
html_theme_options = {
    "description": "Secure phone lifecycle management API",
    "github_user": "nick",
    "github_repo": "eyemeeye",
    "fixed_sidebar": True,
}

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "special-members": "__init__",
}
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "flask": ("https://flask.palletsprojects.com/en/stable/", None),
}
