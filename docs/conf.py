# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
#Defined top level to allow for entire documentation to see
rst_epilog = """ 
.. |appname| replace:: Kitchen Management Suite
"""
import sys
import os
PROJROOT = "../"#"../../src"#Very sensitive path, bad programming practice
sys.path.insert(0, os.path.abspath("../src"))#Allowes sphinx to loop through src directory
sys.path.insert(1, os.path.abspath("../docs"))#Allowes sphinx to loop through docs directory



project = 'KMS'
copyright = '2025, Everyone In Da Group'
author = 'Arya, Mark, Noah, Rohan, & Thomas'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary'
]

autodoc_default_options = {#Every time auto summary in used to create a summary of a file
    'members': True,          # same as :members: #### It will also generate summary for each function
    'undoc-members': True,    # same as :undoc-members:
    'show-inheritance': True, # same as :show-inheritance:
    'inherited-members': True # optional, include inherited members
}


autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['erd']#So that the latest generated erd can be used