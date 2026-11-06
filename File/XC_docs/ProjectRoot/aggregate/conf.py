"""聚合站点配置：只做导航，不引入任何子工程源码。"""

project = "感知文档汇总平台"
copyright = "2026, author"
author = "author"
release = "1.0"

extensions = [
    "myst_parser",
]

myst_enable_extensions = ["colon_fence"]
source_suffix = {".md": "markdown"}
master_doc = "index"
exclude_patterns = ["_build"]

# 聚合层不参与编号
numfig = False

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_js_files = ["custom_search.js"]
