import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'QakeAPI'
copyright = '2024, Craxti'
author = 'Craxti'
release = '1.0.3'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

autodoc_typehints = 'description'
autodoc_member_order = 'bysource'
add_module_names = False 