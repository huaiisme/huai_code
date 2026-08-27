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
IMG_RELATIVE_PREFIX = ""
# ========== 解析逻辑 ==========
def parse_chest_entry(value):
    """解析宝箱配置：
    - 纯数字：返回(数量, False)
    - 列表[数量, 布尔]：返回(数量, 布尔状态)
    """
    # 数组格式：[数量, 完成状态]
    if isinstance(value, list):
        count = int(value[0])
        done = bool(value[1]) if len(value) > 1 else False
        return count, done
    # 简写：纯数字，默认未完成
    if isinstance(value, (int, float, str)):
        return int(value), False
    # 其他异常类型容错，避免崩溃
    return 0, False

def parse_item_entry(entry):
    """解析物品配置：
    - 纯字符串：返回(名称, False)
    - 列表[名称, 布尔]：返回(名称, 布尔状态)
    """
    # 数组格式：[物品名, 完成状态]
    if isinstance(entry, list):
        name = str(entry[0])
        done = bool(entry[1]) if len(entry) > 1 else False
        return name, done
    # 简写：纯字符串，默认未完成
    if isinstance(entry, str):
        return entry, False
    # 异常类型容错
    return str(entry), False

# ========== 生成逻辑 ==========
def generate_area_table(area):
    # 1. 宝箱列表
    chest_items = []
    for grade, value in area["chests"].items():
        count, done = parse_chest_entry(value)
        label = CHEST_ICONS.get(grade, grade)
        check = "[x]" if done else "[ ]"
        chest_items.append(f"    - {check} {label}：{count} 个")
    chest_block = "\n".join(chest_items)

    # 2. 物品列表
    item_block = ""
    if "items" in area and area["items"]:
        item_lines = []
        for entry in area["items"]:
            name, done = parse_item_entry(entry)
            check = "[x]" if done else "[ ]"
            item_lines.append(f"    - {check} 📦 {name}")
        item_block = "\n".join(item_lines)

    img_path = f"{IMG_RELATIVE_PREFIX}{area['map']}"

    lines = []
    lines.append("```{list-table}")
    lines.append(":header-rows: 1")
    lines.append(":align: center")
    lines.append(":header-aligns: center center")
    lines.append(":column-aligns: center center")
    lines.append(":widths: 1 1")
    lines.append("")
    lines.append("* - 地图示意")
    lines.append("  - 详情说明")
    lines.append(f"* - ![{area['name']}地图]({img_path}){{width={area['map_width']}px}}")
    lines.append(f"  - **所属区域**：{area['region_full']}")
    lines.append("")
    lines.append(f"    **城镇名称**：{area['name']}")
    lines.append("")
    lines.append(f"    **对应角色**：{area['character']}")
    lines.append("")
    lines.append("    ---")
    lines.append("")
    lines.append("    **宝箱完成情况**")
    lines.append(chest_block)
    
    if item_block:
        lines.append("")
        lines.append("    ---")
        lines.append("")
        lines.append("    **未获取道具**")
        lines.append(item_block)

    lines.append("```")
    return "\n".join(lines)


def generate_region_folder(region):
    region_dir = OUTPUT_ROOT / region["name"]
    region_dir.mkdir(parents=True, exist_ok=True)

    output = []
    heading = "#" * region["level"] + " " + region["name"]
    output.append(heading)
    output.append("")

    for area in region.get("areas", []):
        table = generate_area_table(area)
        output.append(table)
        output.append("")

    file_name = f"{region['name']}.md"
    file_path = region_dir / file_name
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print(f"✅ 生成：{file_path}（含 {len(region['areas'])} 个区域）")


def main():
    if not DATA_FILE.exists():
        print(f"❌ 数据文件不存在：{DATA_FILE}")
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ YAML 解析失败：{e}")
        return

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    regions = data.get("regions", [])
    for region in regions:
        generate_region_folder(region)

    print(f"\n🎉 全部生成完成")
    print(f"   大区数量：{len(regions)}")
    print(f"   输出根目录：{OUTPUT_ROOT.resolve()}")


if __name__ == "__main__":
    main()