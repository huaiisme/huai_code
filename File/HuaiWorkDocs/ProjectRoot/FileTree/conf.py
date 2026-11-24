"""Sphinx configuration for the HuaiDocs in FileTree."""

project = "Filetree_Sphinx"
copyright = "2026, Huai"
author = "Huai"
release = "0.1.0"

extensions = [
    "myst_parser",
    "sphinx.ext.intersphinx",
    "sphinx_multitoc_numbering",
    "sphinx_copybutton",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "linkify", # 链接
]

source_suffix = {".md": "markdown"}
master_doc = "index"
exclude_patterns = ["_build"]

# ---- 编号：本项目内部独立计数，CODE 1.1 / CODE 1.2 ... ----
numfig = True
numfig_secnum_depth = 1
numfig_format = {
    "code-block": "代码%s",
    "figure": "图%s",
    "table": "表%s",
}

# ---- 跨项目引用（mapping key 必须全小写）----
# intersphinx_mapping = {
#     "bevfusion": ("../BevFusion/_build/html", "../BevFusion/_build/html/objects.inv"),
#     "filetree": ("../FileTree/_build/html", "../FileTree/_build/html/objects.inv"),
# }

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["custom-admonition.css"]
