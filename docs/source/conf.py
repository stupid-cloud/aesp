# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os 
import sys
project = 'AESP'
copyright = '2025, C.L. Qin'
author = 'C.L. Qin'
release = 'v0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # "deepmodeling_sphinx",
    "dargs.sphinx",
    # "myst_parser",
    "sphinx_rtd_theme",
    # "sphinx.ext.viewcode",
    # "sphinx.ext.intersphinx",
    # "numpydoc",
    # "sphinx.ext.autosummary",
    # "sphinxarg.ext",
]

templates_path = ['_templates']
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = []


autodoc_default_flags = ["members"]
autosummary_generate = True
master_doc = "index"

def run_apidoc(_):
    from sphinx.ext.apidoc import (
        main,
    )
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", '..'))
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    module = os.path.join(cur_dir, '..', '..', "src", "aesp")
    main(
        [
            "-M",
            "--tocfile",
            "api",
            "-H",
            "AESP API",
            "-o",
            os.path.join(cur_dir, "api"),
            module,
            "--force",
        ]
    )

def setup(app):
    app.connect("builder-inited", run_apidoc)

# intersphinx_mapping = {
#     "python": ("https://docs.python.org/", None),
#     "numpy": ("https://docs.scipy.org/doc/numpy/", None),
#     "dargs": ("https://docs.deepmodeling.com/projects/dargs/en/latest/", None),
#     "dflow": ("https://deepmodeling.com/dflow/", None),
#     "dpdata": ("https://docs.deepmodeling.com/projects/dpdata/en/latest/", None),
# }
