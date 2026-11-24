#!/usr/bin/env python3
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
