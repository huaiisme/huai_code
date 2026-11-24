#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键生成 ProjectRoot 多子工程 Sphinx 文档骨架。

三个子项目：BevFusion / FileTree / MultiSensorPostFusion
用法：python3 create_docs_tree.py
"""

from pathlib import Path

# ============================================================
# 1. 顶层文件
# ============================================================

GITIGNORE = """# Sphinx build output
_build/
*/_build/

# python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# editor
.vscode/
.idea/
.DS_Store
"""

MAKEFILE = """AGG_OUT := aggregate/_build/html
PROJECTS := BevFusion FileTree MultiSensorPostFusion

.PHONY: all stage1 stage2 build aggregate clean help

help:
\t@echo "===== 命令列表 ====="
\t@echo "  make BevFusion                 单独构建 BevFusion"
\t@echo "  make FileTree                  单独构建 FileTree"
\t@echo "  make MultiSensorPostFusion     单独构建 MultiSensorPostFusion"
\t@echo "  make all                       全量构建 + 聚合站点 + 合并搜索索引"
\t@echo "  make clean                     清空所有构建产物"

BevFusion:
\tcd BevFusion && sphinx-build . _build/html

FileTree:
\tcd FileTree && sphinx-build . _build/html

MultiSensorPostFusion:
\tcd MultiSensorPostFusion && sphinx-build . _build/html

# 第一轮：先让每个子工程产出一份 objects.inv，供其他工程 intersphinx 引用
stage1:
\t@for p in $(PROJECTS); do \\
\t\techo ">> 第一轮（生成 inventory）：$$p"; \\
\t\t(cd $$p && sphinx-build -q . _build/html) || true; \\
\tdone

# 第二轮：inventory 齐全后完整构建，消除 intersphinx 找不到对象的告警
stage2:
\t@for p in $(PROJECTS); do \\
\t\techo ">> 第二轮（完整构建）：$$p"; \\
\t\t(cd $$p && sphinx-build . _build/html); \\
\tdone

build: stage1 stage2

aggregate:
\trm -rf $(AGG_OUT)
\tsphinx-build aggregate $(AGG_OUT)
\tcp -r BevFusion/_build/html $(AGG_OUT)/bevfusion
\tcp -r FileTree/_build/html $(AGG_OUT)/filetree
\tcp -r MultiSensorPostFusion/_build/html $(AGG_OUT)/multisensorpostfusion

all: build aggregate
\tpython3 merge_search_index.py
\t@echo "聚合站点输出目录: $(AGG_OUT)"

clean:
\trm -rf BevFusion/_build FileTree/_build MultiSensorPostFusion/_build aggregate/_build
"""

# ============================================================
# 2. 子工程公共配置模板
# ============================================================

CONF_TEMPLATE = '''"""Sphinx configuration for the {project} sub-project."""

project = "{project}"
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

source_suffix = {{".md": "markdown"}}
master_doc = "index"
exclude_patterns = ["_build"]

# ---- 编号：本项目内部独立计数，CODE 1.1 / CODE 1.2 ... ----
numfig = True
numfig_secnum_depth = 1
numfig_format = {{
    "code-block": "CODE %s",
    "figure": "Fig. %s",
    "table": "Table %s",
}}

# ---- 跨项目引用（mapping key 必须全小写）----
intersphinx_mapping = {{
{intersphinx_items}
}}

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
'''

AGGREGATE_CONF = '''"""聚合站点配置：只做导航，不引入任何子工程源码。"""

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
'''

AGGREGATE_INDEX = """# 感知文档汇总平台

> 三个子项目各自独立编号，CODE 在本项目内从 1 开始，互不干扰。

<ul>
  <li><a href="./bevfusion/index.html">BevFusion 文档</a></li>
  <li><a href="./filetree/index.html">FileTree 文档</a></li>
  <li><a href="./multisensorpostfusion/index.html">MultiSensorPostFusion 文档</a></li>
</ul>
"""

SUBPROJECT_INDEX = """# {title}

```{{toctree}}
:numbered:
:maxdepth: 2

docs/ros_env.md
```
"""

ROS_ENV_MD = """# Ubuntu 20.04 ROS1 环境配置

## 安装 ROS Noetic

```{code-block} shell
:linenos:
:caption: 安装 ROS Noetic
:name: ros-noetic-install

sudo apt install ros-noetic-desktop-full
```

引用写法：{numref}`%s <ros-noetic-install>`

## 初始化工作空间

```{code-block} shell
:linenos:
:caption: 初始化 catkin 工作空间
:name: catkin-init

mkdir -p ~/catkin_ws/src
cd ~/catkin_ws
catkin_make
```

引用写法：{numref}`%s <catkin-init>`
"""

CUSTOM_SEARCH_JS = """/* 聚合站点搜索结果按项目来源着色 */
document.addEventListener("DOMContentLoaded", function () {
  var container = document.querySelector(".search");
  if (!container) return;

  var observer = new MutationObserver(function () {
    var items = container.querySelectorAll(".search-result");
    items.forEach(function (el) {
      var title = el.querySelector(".search-result-title");
      if (!title) return;
      if (/^\\[(BevFusion|FileTree|MultiSensorPostFusion)\\]/.test(title.textContent || "")) {
        el.style.borderLeft = "4px solid #2980b9";
        el.style.paddingLeft = "8px";
      }
    });
  });

  observer.observe(container, { childList: true, subtree: true });
});
"""

# ============================================================
# 3. 合并搜索索引脚本
# ============================================================

MERGE_SEARCH_INDEX = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把聚合站点与三个子工程的搜索索引合并成一份全局索引。

Sphinx 的 searchindex 有两个落盘形态，这里都支持：
    searchindex.js    ->  Search.setIndex({...})       （较新版本默认）
    searchindex.json  ->  裸 JSON                      （较老版本）
索引内部字段：
    docnames     [docName, ...]                       文档内部名，前缀化后即是访问路径
    filenames    [file.md, ...]                       源文件路径，与 docnames 一一对应
    titles       [title, ...]
    terms        {词: 文档下标} 或 {词: [文档下标, ...]}  旧版是 {词: {docName: 次数}}
    titleterms   同 terms
    alltitles    {标题: [[文档下标, 锚点id], ...]}
    indexentries {词条: [[文档下标, 锚点id, 是否主条目], ...]}
    objects      {域前缀: [[文档下标, objName下标, 优先级, 锚点, 名字], ...]}

合并策略：
    1. 每个子工程的 docnames / filenames 前加目录前缀（bevfusion/...）；
    2. 所有“文档下标”统一加偏移量，保证跨索引的下标不冲突；
    3. 输出写成 searchindex.js，overwrite 聚合站点自身的那份，
       聚合站点的 search.html 通过 Search.loadIndex("searchindex.js") 直接加载。
"""

import json
from pathlib import Path

AGG_HTML = Path("aggregate/_build/html")

# (目录前缀, 站点输出目录)；前缀为空表示聚合站点自己的页面
SOURCES = [
    ("", AGG_HTML),
    ("bevfusion", Path("BevFusion/_build/html")),
    ("filetree", Path("FileTree/_build/html")),
    ("multisensorpostfusion", Path("MultiSensorPostFusion/_build/html")),
]

INDEX_FILES = ("searchindex.js", "searchindex.json")


def find_index_html_dir(dirpath):
    """定位某个输出目录里的索引文件。"""
    for name in INDEX_FILES:
        path = dirpath / name
        if path.exists():
            return path
    return None


def load_index(path):
    """读取索引文件，js 形态要剥掉 Search.setIndex(...) 外壳。"""
    raw = path.read_text(encoding="utf-8")
    if path.suffix == ".js":
        raw = raw[raw.index("(") + 1: raw.rindex(")")]
    return json.loads(raw)


def is_legacy(terms):
    """判断 terms 是旧格式（值为 {docName: 次数}）还是新格式（值为文档下标）。"""
    for value in terms.values():
        return isinstance(value, dict)
    return False


def as_list(value):
    """把“单值或列表”统一成列表。"""
    return value if isinstance(value, list) else [value]


def offset_value(value, offset):
    """新格式：文档下标或下标列表，整体加上偏移量。"""
    if isinstance(value, list):
        return [item + offset for item in value]
    return value + offset


def merge_doc_indices(existing, value, offset):
    """新格式合并：同名词条把各工程的文档下标并成一个去重列表。"""
    shifted = offset_value(value, offset)
    if existing is None:
        return shifted
    return sorted(set(as_list(existing) + as_list(shifted)))


MERGED_TEMPLATE = {
    "docnames": list,
    "filenames": list,
    "titles": list,
    "terms": dict,
    "titleterms": dict,
    "alltitles": dict,
    "indexentries": dict,
    "objects": dict,
    "objnames": dict,
    "objtypes": dict,
    "envversion": dict,
}


def merge_one(merged, data, prefix, legacy):
    """把单份索引并入 merged。"""
    docnames = list(data.get("docnames", []))
    offset = len(merged["docnames"])

    merged["docnames"].extend(f"{prefix}/{d}" if prefix else d for d in docnames)
    merged["filenames"].extend(
        f"{prefix}/{f}" if prefix else f for f in data.get("filenames", [])
    )
    merged["titles"].extend(data.get("titles", []))

    for word, value in data.get("terms", {}).items():
        if legacy:
            target = merged["terms"].setdefault(word, {})
            for name, count in value.items():
                target[f"{prefix}/{name}" if prefix else name] = count
        else:
            merged["terms"][word] = merge_doc_indices(
                merged["terms"].get(word), value, offset
            )

    for word, value in data.get("titleterms", {}).items():
        if legacy:
            bucket = merged["titleterms"].setdefault(word, [])
            bucket.extend(f"{prefix}/{name}" if prefix else name for name in value)
        else:
            merged["titleterms"][word] = merge_doc_indices(
                merged["titleterms"].get(word), value, offset
            )

    for title, refs in data.get("alltitles", {}).items():
        bucket = merged["alltitles"].setdefault(title, [])
        bucket.extend([[idx + offset, anchor] for idx, anchor in refs])

    for entry, refs in data.get("indexentries", {}).items():
        bucket = merged["indexentries"].setdefault(entry, [])
        bucket.extend(
            [[idx + offset, anchor, flag] for idx, anchor, flag in refs]
        )

    for domain, entries in data.get("objects", {}).items():
        bucket = merged["objects"].setdefault(domain, [])
        bucket.extend(
            [[item[0] + offset] + item[1:] for item in entries]
        )

    for field in ("objnames", "objtypes", "envversion"):
        merged[field].update(data.get(field, {}))


def main():
    merged = {k: factory() for k, factory in MERGED_TEMPLATE.items()}

    legacy = None
    used = 0
    for prefix, html_dir in SOURCES:
        index_path = find_index_html_dir(html_dir)
        if index_path is None:
            print(f"跳过 {prefix or 'aggregate'}：{html_dir} 下没有搜索索引")
            continue

        data = load_index(index_path)
        current = is_legacy(data.get("terms", {}))
        if legacy is None:
            legacy = current
        elif legacy != current:
            print(f"警告：{prefix} 的索引格式与其他工程不一致，请统一 Sphinx 版本后重试")
            continue

        merge_one(merged, data, prefix, legacy)
        used += 1

    out = AGG_HTML / "searchindex.js"
    out.write_text(
        "Search.setIndex(" + json.dumps(merged, ensure_ascii=False) + ")",
        encoding="utf-8",
    )

    print(f"合并 {used} 份索引 -> {out}")
    print(f"文档数 {len(merged['docnames'])}，词条数 {len(merged['terms'])}")


if __name__ == "__main__":
    main()
'''

# ============================================================
# 4. 项目定义
# ============================================================

PROJECTS = [
    # 目录名, 页面标题
    ("BevFusion", "BevFusion 感知文档"),
    ("FileTree", "FileTree 工具文档"),
    ("MultiSensorPostFusion", "MultiSensorPostFusion 多传感器融合文档"),
]


def build_intersphinx(project_name):
    """生成某工程对另外两个工程的 intersphinx 映射。"""
    items = []
    for other, _ in PROJECTS:
        if other == project_name:
            continue
        html = f"../{other}/_build/html"
        items.append(f'    "{other.lower()}": ("{html}", "{html}/objects.inv"),')
    return "\n".join(items)


def main():
    root = Path("ProjectRoot").resolve()
    root.mkdir(parents=True, exist_ok=True)

    def write(rel_path, content):
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"生成 {path.relative_to(root)}")

    write(".gitignore", GITIGNORE)
    write("Makefile", MAKEFILE)
    write("merge_search_index.py", MERGE_SEARCH_INDEX)

    for name, title in PROJECTS:
        write(f"{name}/conf.py", CONF_TEMPLATE.format(
            project=name,
            intersphinx_items=build_intersphinx(name),
        ))
        write(f"{name}/index.md", SUBPROJECT_INDEX.format(title=title))
        write(f"{name}/docs/ros_env.md", ROS_ENV_MD)
        (root / name / "_static").mkdir(parents=True, exist_ok=True)

    write("aggregate/conf.py", AGGREGATE_CONF)
    write("aggregate/index.md", AGGREGATE_INDEX)
    write("aggregate/_static/custom_search.js", CUSTOM_SEARCH_JS)

    print(f"\n完成：{root}")


if __name__ == "__main__":
    main()