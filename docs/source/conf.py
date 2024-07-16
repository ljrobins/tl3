# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

from datetime import date

project = 'TL3'
copyright = f'2024-{date.today().year}, Liam Robinson'
author = 'Liam Robinson'
version = '0.0.3'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx_gallery.gen_gallery',
    'sphinx_copybutton',
    "sphinx.ext.viewcode",
]
templates_path = ['_templates']
html_css_files = [
    'css/custom.css',
]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']
navigation_with_keys = False

html_show_sourcelink = False

# Gallery options
sphinx_gallery_conf = {
    'gallery_dirs': ['gallery'],
    'examples_dirs': ['../../examples'],
    'filename_pattern': '/*.py',
    'download_all_examples': False,
    'image_scrapers': ['matplotlib'],
    'matplotlib_animations': True,
    'thumbnail_size': (333, 250),
    'image_srcset': ['2x'],
}

# Doing things I probably shouldn't here
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join('..', '..')))
