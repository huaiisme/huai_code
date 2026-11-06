"""Sphinx configuration for the FileTree sub-project."""

project = "FileTree"
copyright = "2026, author"
author = "author"
release = "0.1.0"

extensions = [
    "myst_parser",
    "sphinx.ext.intersphinx",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

source_suffix = {".md": "markdown"}
master_doc = "index"
exclude_patterns = ["_build"]

# ---- 编号：本项目内部独立计数，CODE 1.1 / CODE 1.2 ... ----
numfig = True
numfig_secnum_depth = 1
numfig_format = {
    "code-block": "CODE %s",
    "figure": "Fig. %s",
    "table": "Table %s",
}

# ---- 跨项目引用（mapping key 必须全小写）----
intersphinx_mapping = {
    "bevfusion": ("../BevFusion/_build/html", "../BevFusion/_build/html/objects.inv"),
    "multisensorpostfusion": ("../MultiSensorPostFusion/_build/html", "../MultiSensorPostFusion/_build/html/objects.inv"),
}

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
