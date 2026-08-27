import yaml
from pathlib import Path


# ========== 配置项 ==========
CHEST_ICONS = {
    "purple": "🔮 紫色宝箱",
    "gold": "👑 金色宝箱",
    "silver": "🥈 银色宝箱"
}

DATA_FILE = Path("regions.yaml")
OUTPUT_ROOT = Path("regions")
# 图片公共前缀：统一到 region 根目录，后续自动拼接大区名称
IMG_PATH_PREFIX = "../../../../../../_static/Games/OctopathTraveler/OctopathTravelerI/region"
DEFAULT_MAP_WIDTH = 320


# ========== 通用状态解析 ==========
def _parse_status(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "checked"
    return False


def parse_chest_entry(value):
    if isinstance(value, list):
        count = int(value[0])
        done = _parse_status(value[1]) if len(value) > 1 else False
        return count, done
    if isinstance(value, (int, float, str)):
        return int(value), False
    return 0, False


def parse_item_entry(entry):
    if isinstance(entry, list):
        name = str(entry[0])
        done = _parse_status(entry[1]) if len(entry) > 1 else False
        return name, done
    if isinstance(entry, str):
        return entry, False
    return str(entry), False


# ========== 词汇解析 ==========
def parse_vocab_entry(entry):
    if isinstance(entry, list):
        word = str(entry[0]).strip() if len(entry) > 0 else ""
        meaning = str(entry[1]).strip() if len(entry) > 1 else ""
        return {"word": word, "pos": "", "meaning": meaning, "scene": ""}
    if isinstance(entry, dict):
        return {
            "word": str(entry.get("word", "")).strip(),
            "pos": str(entry.get("pos", "")).strip(),
            "meaning": str(entry.get("meaning", "")).strip(),
            "scene": str(entry.get("scene", "")).strip(),
        }
    return {"word": str(entry).strip(), "pos": "", "meaning": "", "scene": ""}


# ========== 句子解析 ==========
def parse_sentence_entry(entry):
    if isinstance(entry, list):
        sentence = str(entry[0]).strip() if len(entry) > 0 else ""
        translation = str(entry[1]).strip() if len(entry) > 1 else ""
        return {"sentence": sentence, "translation": translation, "scene": ""}
    if isinstance(entry, dict):
        return {
            "sentence": str(entry.get("sentence", "")).strip(),
            "translation": str(entry.get("translation", "")).strip(),
            "scene": str(entry.get("scene", "")).strip(),
        }
    return {"sentence": str(entry).strip(), "translation": "", "scene": ""}


# ========== 生成单区域表格 ==========
def generate_area_table(area, region_name):
    # 自动拼接：公共前缀 + 大区名称 + 图片文件名
    img_full_path = f"{IMG_PATH_PREFIX}/{region_name}/{area['map']}"
    map_width = area.get("map_width", DEFAULT_MAP_WIDTH)

    # 1. 宝箱列表
    chest_lines = []
    for grade, value in area["chests"].items():
        count, done = parse_chest_entry(value)
        label = CHEST_ICONS.get(grade, grade)
        checked_attr = "checked" if done else ""
        chest_lines.append(
            f'<input type="checkbox" {checked_attr} style="vertical-align: middle; margin-right: 8px;">{label}：{count} 个'
        )
    chest_block = "<br>".join(chest_lines)

    # 2. 道具列表
    item_block = ""
    if "items" in area and area["items"]:
        item_lines = []
        for entry in area["items"]:
            name, done = parse_item_entry(entry)
            checked_attr = "checked" if done else ""
            item_lines.append(
                f'<input type="checkbox" {checked_attr} style="vertical-align: middle; margin-right: 8px;">📦 {name}'
            )
        item_block = "<br>".join(item_lines)

    # 3. 怪物列表
    monster_block = ""
    if "monsters" in area and area["monsters"]:
        monster_lines = []
        for entry in area["monsters"]:
            name, done = parse_item_entry(entry)
            checked_attr = "checked" if done else ""
            monster_lines.append(
                f'<input type="checkbox" {checked_attr} style="vertical-align: middle; margin-right: 8px;">👾 {name}'
            )
        monster_block = "<br>".join(monster_lines)

    # 4. 生词词汇（两列内嵌表格）
    vocab_block = ""
    if "vocab" in area and area["vocab"]:
        vocab_rows = []
        for entry in area["vocab"]:
            v = parse_vocab_entry(entry)
            left_parts = []
            if v["word"]:
                left_parts.append(f'<strong>{v["word"]}</strong>')
            if v["pos"]:
                left_parts.append(f'<span style="color: #666; font-size: 0.9em; margin-left: 6px;">{v["pos"]}</span>')
            left_cell = "".join(left_parts)

            right_parts = []
            if v["meaning"]:
                right_parts.append(v["meaning"])
            if v["scene"]:
                right_parts.append(f'<span style="color: #888; font-size: 0.9em; margin-left: 8px;">（{v["scene"]}）</span>')
            right_cell = "".join(right_parts)

            vocab_rows.append(f"  <tr>\n    <td style=\"padding: 6px 10px; border-bottom: 1px solid #f0f2f5;\">{left_cell}</td>\n    <td style=\"padding: 6px 10px; border-bottom: 1px solid #f0f2f5;\">{right_cell}</td>\n  </tr>")

        vocab_table = f'''<table style="width: 100%; border-collapse: collapse; margin-top: 8px;">
  <tr>
    <th style="width: 50%; text-align: left; background-color: #f8f9fa; padding: 8px 10px; border-bottom: 1px solid #e9ecef; font-weight: 600;">单词</th>
    <th style="text-align: left; background-color: #f8f9fa; padding: 8px 10px; border-bottom: 1px solid #e9ecef; font-weight: 600;">释义</th>
  </tr>
{"".join(vocab_rows)}
</table>'''
        vocab_block = vocab_table

    # 5. 精选句子
    sentence_block = ""
    if "sentences" in area and area["sentences"]:
        sentence_items = []
        for entry in area["sentences"]:
            s = parse_sentence_entry(entry)
            parts = []
            if s["sentence"]:
                parts.append(f'<span style="font-style: italic; color: #333; line-height: 1.3;">{s["sentence"]}</span>')
            if s["translation"]:
                parts.append(f'<div style="color: #555; margin-top: 1px; line-height: 1.3;">{s["translation"]}</div>')
            if s["scene"]:
                parts.append(f'<div style="color: #888; font-size: 0.9em; margin-top: 1px; line-height: 1.3;">—— {s["scene"]}</div>')
            sentence_items.append(f'<div style="margin-bottom: 4px;">{"".join(parts)}</div>')
        sentence_block = "".join(sentence_items)

    # 6. 拼接详情内容
    detail_parts = [f"<strong>宝箱完成情况</strong><br>{chest_block}"]
    if item_block:
        detail_parts.append(f"<strong>未获取道具</strong><br>{item_block}")
    if monster_block:
        detail_parts.append(f"<strong>怪物情况</strong><br>{monster_block}")
    if vocab_block:
        detail_parts.append(f"<strong>生词词汇</strong>{vocab_block}")
    if sentence_block:
        detail_parts.append(f"<strong>精选句子</strong><br>{sentence_block}")
    detail_content = "<br><br>".join(detail_parts)

    # 7. 构建外层主表格（所属区域用大区名替换）
    table_html = f'''<table style="border-collapse: collapse; width: 100%; margin: 16px 0; font-family: inherit;">
  <tr>
    <th style="width: 50%; text-align: center; background-color: #f8f9fa; padding: 12px 16px; border: 1px solid #e9ecef; font-size: 1.1em;">地点示意</th>
    <th style="text-align: center; background-color: #f8f9fa; padding: 12px 16px; border: 1px solid #e9ecef; font-size: 1.1em;">地点说明</th>
  </tr>
  <tr>
    <td style="text-align: center; vertical-align: middle; padding: 16px; border: 1px solid #e9ecef;">
      <img src="{img_full_path}" alt="{area['name']}地图" width="{map_width}" style="vertical-align: middle; border-radius: 4px;">
    </td>
    <td style="text-align: center; vertical-align: middle; padding: 16px; border: 1px solid #e9ecef; line-height: 2;">
      <strong>所属区域</strong>：{region_name}<br>
      <strong>城镇名称</strong>：{area['name']}
    </td>
  </tr>
  <tr>
    <td colspan="2" style="background-color: #f8f9fa; padding: 12px 16px; border: 1px solid #e9ecef; font-size: 1.1em; font-weight: bold;">
      详情说明
    </td>
  </tr>
  <tr>
    <td colspan="2" style="padding: 16px; border: 1px solid #e9ecef; line-height: 1.7;">
      {detail_content}
    </td>
  </tr>
</table>'''

    return table_html


# ========== 批量生成 ==========
def generate_region_folder(region):
    region_dir = OUTPUT_ROOT / region["name"]
    region_dir.mkdir(parents=True, exist_ok=True)

    output = []
    heading = "#" * region.get("level", 2) + " " + region["name"]
    output.append(heading)
    output.append("")

    for area in region.get("areas", []):
        # 传入当前大区名称，用于图片路径 + 所属区域显示
        table = generate_area_table(area, region["name"])
        output.append(table)
        output.append("")

    file_name = f"{region['name']}.md"
    file_path = region_dir / file_name
    file_path.write_text("\n".join(output), encoding="utf-8")
    print(f"✅ 生成：{file_path}")


def main():
    if not DATA_FILE.exists():
        print(f"❌ 配置文件不存在：{DATA_FILE}")
        return

    data = yaml.safe_load(DATA_FILE.read_text(encoding="utf-8"))
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    for region in data.get("regions", []):
        generate_region_folder(region)

    print("\n🎉 全部生成完成")


if __name__ == "__main__":
    main()
