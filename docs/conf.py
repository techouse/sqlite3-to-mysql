# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import re
import sys
from pathlib import Path


sys.path.insert(0, os.path.abspath("../src"))

_ROOT = Path(__file__).resolve().parents[1]
_ver_file = _ROOT / "src" / "sqlite3_to_mysql" / "__init__.py"
_m = re.search(r'^__version__\s*=\s*[\'"]([^\'"]+)[\'"]', _ver_file.read_text(encoding="utf-8"), re.M)
__version__ = _m.group(1) if _m else "0+unknown"


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "sqlite3-to-mysql"
copyright = "%Y, Klemen Tusar"
author = "Klemen Tusar"
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode", "sphinx.ext.napoleon"]

napoleon_google_docstring = True
napoleon_include_init_with_doc = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
