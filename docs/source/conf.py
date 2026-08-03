# -- Project information -----------------------------------------------------
project = 'Huai Knowledge Base'
copyright = '2026, Huai'
author = 'Huai'
release = '0.1'

# -- General configuration ---------------------------------------------------
extensions = [
    "myst_parser",  # Markdown解析核心
    "sphinx_rtd_theme",
    'sphinx.ext.autodoc',      # 自动提取代码文档
    'sphinx.ext.viewcode',     # 显示源码链接
    'sphinx.ext.todo',         # TODO列表
    'sphinx.ext.mathjax',      # 数学公式支持
    'sphinx_copybutton',       # 代码块复制按钮（需pip安装）
]

# 支持的文件后缀：以md为主，保留rst兼容能力
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# MyST 增强功能（写笔记非常实用）
myst_enable_extensions = [
    "colon_fence",    # 用:::替代```写指令，更符合Markdown习惯
    "linkify",        # 自动识别网址链接
    "tasklist",       # 支持任务列表 [ ] [x]
    "html_image",     # 支持HTML图片标签
]


templates_path = ['_templates']
exclude_patterns = []
language = 'zh_CN'

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'  # Read the Docs主题，最经典的文档主题
html_static_path = ['_static']
html_css_files = ['custom.css']  # 自定义样式

# 显示"上一页/下一页"
html_show_sourcelink = True

# TODO扩展配置
todo_include_todos = True