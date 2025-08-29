# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys


from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from importlib.metadata import PackageNotFoundError, version as pkg_version


def _version_from_source() -> str:
    init_py = SRC / "sqlite3_to_mysql" / "__init__.py"
    m = re.search(r'^__version__\s*=\s*[\'"]([^\'"]+)[\'"]', init_py.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else "0+unknown"


try:
    __version__ = pkg_version("sqlite3-to-mysql")
except PackageNotFoundError:
    __version__ = _version_from_source()


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "sqlite3-to-mysql"
copyright = "2024, Klemen Tusar"
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
