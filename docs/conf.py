# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------

project = 'QakeAPI'
copyright = '2024, QakeAPI Team'
author = 'QakeAPI Team'

# The full version, including alpha/beta/rc tags
release = '1.1.2'
version = '1.1.2'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.githubpages',
    'sphinx_rtd_theme',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.doctest',
    'sphinx.ext.mathjax',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
    'github_url': 'https://github.com/Craxti/qakeapi',
    'logo_only': False,
    'display_version': True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom CSS
html_css_files = [
    'custom.css',
]

# -- Options for autodoc ----------------------------------------------------

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

autodoc_mock_imports = [
    'uvicorn',
    'pydantic',
    'ariadne',
    'redis',
    'psutil',
    'aiofiles',
    'jinja2',
    'httpx',
    'websockets',
]

# -- Options for intersphinx -------------------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'asyncio': ('https://docs.python.org/3/library/asyncio.html', None),
    'pydantic': ('https://pydantic-docs.helpmanual.io/', None),
    'fastapi': ('https://fastapi.tiangolo.com/', None),
}

# -- Options for todo extension ----------------------------------------------

todo_include_todos = True

# -- Options for napoleon extension ------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_attr_annotations = True

# -- Options for coverage extension ------------------------------------------

coverage_show_missing_items = True

# -- Project-specific settings -----------------------------------------------

# Add any project-specific settings here
html_context = {
    'display_github': True,
    'github_user': 'Craxti',
    'github_repo': 'qakeapi',
    'github_version': 'main',
    'conf_py_path': '/docs/',
    'source_suffix': '.rst',
}

# -- Extension configuration -------------------------------------------------

def setup(app):
    app.add_css_file('custom.css') 