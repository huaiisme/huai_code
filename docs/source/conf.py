# -- Project information -----------------------------------------------------
project = 'Huai Knowledge Base'
copyright = '2026, Huai'
author = 'Huai'
release = '0.1'

# -- General configuration ---------------------------------------------------
extensions = [
    "myst_parser",               # Markdown 解析核心
    'sphinx.ext.autodoc',        # 自动提取代码文档
    'sphinx.ext.viewcode',       # 显示源码链接
    'sphinx.ext.todo',           # TODO 列表
    'sphinx.ext.mathjax',        # 数学公式支持
    'sphinx_copybutton',         # 代码块复制按钮
]

# 支持的文件后缀：以md为主，保留rst兼容能力
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# MyST 增强功能（完整适配 Markdown 优雅撰写）
myst_enable_extensions = [
    "colon_fence",      # 用 ::: 替代 ``` 写提示框，更符合 Markdown 习惯
    "linkify",          # 自动识别网址并转为链接
    "tasklist",         # 支持 [ ] [x] 任务列表
    "html_image",       # 支持 HTML 图片标签
    "deflist",          # 新增：定义列表，术语解释神器
    "attrs_block",      # 新增：给段落/代码块加自定义属性、锚点
    "smartquotes",      # 新增：智能替换直引号为弯引号，排版更美观
]

myst_linkify_options = {
    "fuzzyLink": True,    # 识别不带 http 的纯域名，如 github.com
    "fuzzyEmail": True,   # 识别纯文本邮箱，自动加上 mailto: 链接
    "fuzzyIP": False      # 不识别纯 IP 地址
}

# 全局开启图表、表格、代码块自动编号
numfig = True

# 修正后的编号格式（全部使用 %s 字符串占位符）
numfig_format = {
    'figure': '图 %s. ',      # 图片：图 1. xxx（支持多级编号 图 1.1. xxx）
    'table': '表 %s. ',       # 表格：表 1. xxx
    'code-block': '代码 %s. ' # 代码块：代码 1. xxx
}



# 新增：三级以内标题自动生成锚点，支持跨文档跳转定位
myst_heading_anchors = 3

templates_path = ['_templates']
exclude_patterns = []
language = 'zh_CN'

# 新增：优化中文搜索分词效果
html_search_language = 'zh_CN'

# 新增：图表、代码块自动编号，专业文档更规范
numfig = True

# TODO 扩展配置
todo_include_todos = True
todo_emit_warnings = False  # 新增：避免 TODO 产生构建警告

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = ['custom.css']

# 显示页面源码链接
html_show_sourcelink = True
# 显示上一页/下一页导航
html_show_prev_next = True

# 新增：RTD 主题深度优化（侧边栏+导航+视觉）
html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,       # 外部链接加跳转图标
    'collapse_navigation': False,       # 侧边栏默认展开
    'sticky_navigation': True,          # 侧边栏滚动时固定
    'navigation_depth': 4,              # 侧边栏最多显示四级标题
    'includehidden': True,
    'titles_only': False
}

# 新增：代码复制按钮智能优化（自动去掉命令提示符）
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = False
copybutton_remove_prompts = True