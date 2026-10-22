import json
import os
from scipy.spatial.transform import Rotation
import numpy as np

GT_DIR = "/home/huai/huai_work/data/gt_label_simple/record_2026-06-04-10-19-07"

files = [f for f in os.listdir(GT_DIR) if f.endswith(".json")]
files.sort()

print(f"=== 共找到 {len(files)} 个JSON文件 ===\n")

# 取第一个和最后一个验证
for fname in [files[0], files[-1]]:
    json_path = os.path.join(GT_DIR, fname)
    with open(json_path, 'r') as f:
        data = json.load(f)

    print(f"--- 文件: {fname} ---")
    print(f"外层key: {list(data.keys())}")

    # 时间戳验证
    t_raw = data["timestamp"]
    # 判断位数
    if t_raw > 1e18:
        t_ms = t_raw // 1000000
        t_type = "纳秒(19位)"
    elif t_raw > 1e12:
        t_ms = t_raw
        t_type = "毫秒(13位)"
    else:
        t_ms = int(round(t_raw * 1000))
        t_type = "秒(10位)"
    
    print(f"timestamp原始值: {t_raw} ({t_type})")
    print(f"timestamp (ms): {t_ms}")
    # ego位姿
    print(f"\nego_translation: {data['ego_translation']}")
    print(f"ego_rotation [qw,qx,qy,qz]: {data['ego_rotation']}")
    qw, qx, qy, qz = data["ego_rotation"]
    ego_yaw = Rotation.from_quat([qx, qy, qz, qw]).as_euler("xyz")[2]
    print(f"ego_yaw: {ego_yaw:.3f} rad = {np.rad2deg(ego_yaw):.1f}°")

    # 物体
    print(f"\n共 {len(data['objects'])} 个物体:")
    for i, obj in enumerate(data["objects"][:3]):
        print(f"  [{i+1}] ID={obj['ID']}, category={obj['category']}")
        print(f"      translation: {obj['translation']}")
        print(f"      size [w,l,h]: {obj['size']}")
        qw, qx, qy, qz = obj["rotation"]
        obj_yaw = Rotation.from_quat([qx, qy, qz, qw]).as_euler("xyz")[2]
        print(f"      yaw: {obj_yaw:.3f} rad = {np.rad2deg(obj_yaw):.1f}°")
    if len(data["objects"]) > 3:
        print(f"  ... 还有 {len(data['objects']) - 3} 个")

    print("\n" + "="*60 + "\n")
