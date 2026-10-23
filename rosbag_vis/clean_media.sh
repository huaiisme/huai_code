#!/bin/bash
#
# clean_media.sh
#   删除目标目录下所有 .mp4 和 .png 文件；
#   删除后如果某个文件夹变空（说明它里面全是 .png/.mp4），连文件夹一起删掉。
#
# 用法:
#   ./clean_media.sh [目标目录]     # 不传目录则默认当前目录
#   DRY_RUN=1 ./clean_media.sh xxx  # 只打印要删什么，不真删（预览）
#

set -euo pipefail

TARGET="${1:-.}"

if [ ! -d "$TARGET" ]; then
    echo "错误：目录不存在 -> $TARGET" >&2
    exit 1
fi

# 转成绝对路径，避免后面相对路径混乱
TARGET="$(cd "$TARGET" && pwd)"

# DRY_RUN=1 时只预览
if [ "${DRY_RUN:-0}" = "1" ]; then
    echo "[预览模式] 不会真的删除任何东西"
    echo "目标目录: $TARGET"
    echo
    echo "== 将删除以下 .mp4 / .png 文件 =="
    find "$TARGET" -type f \( -iname "*.mp4" -o -iname "*.png" \)
    echo
    echo "== 删除文件后，以下空文件夹将被删除 =="
    # 先列出会被删的文件，再模拟删完后哪些目录变空
    find "$TARGET" -type f \( -iname "*.mp4" -o -iname "*.png" \) -delete 2>/dev/null || true
    find "$TARGET" -type d -empty
    exit 0
fi

echo "目标目录: $TARGET"
echo

# 1) 删除所有 .mp4 / .png 文件（-delete 自底向上安全删除）
echo "== 删除 .mp4 / .png 文件 =="
find "$TARGET" -type f \( -iname "*.mp4" -o -iname "*.png" \) -print -delete

# 2) 删除因此变空的文件夹（从最深层开始，逐级往上删空目录）
echo
echo "== 删除空文件夹 =="
find "$TARGET" -type d -empty -print -delete

echo
echo "完成。"
