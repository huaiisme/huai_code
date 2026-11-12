"""bag 读取的公共底座：缓存、时间匹配、odom、GT/标签、Pred CSV。

rosbag / cv_bridge 等 ROS 依赖在真正读 bag 的函数内延迟 import，
这样在没有 ROS 的机器上也能导入本模块做纯逻辑/渲染自检。
"""
import os
import pickle

import numpy as np

from utils.tf import odom_pose_to_matrix


# ---------------- 缓存（每个 topic 独立 pkl，放在 {bag名}_cache/ 目录下） ----------------
def _topic_cache_path(bag_path, topic_key):
    bag_abs = os.path.abspath(bag_path)
    bag_name = os.path.basename(bag_abs).replace(".bag", "")
    cache_dir = os.path.join(os.path.dirname(bag_abs), f"{bag_name}_cache")
    safe_topic = topic_key.replace("/", "_").strip("_")
    return os.path.join(cache_dir, f"{bag_name}_{safe_topic}_cache.pkl")


def _load_cached_topic(bag_path, topic_key):
    cache_file = _topic_cache_path(bag_path, topic_key)
    if not os.path.exists(cache_file):
        return None
    with open(cache_file, "rb") as f:
        return pickle.load(f)


def _save_cached_topic(bag_path, topic_key, data):
    cache_file = _topic_cache_path(bag_path, topic_key)
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "wb") as f:
        pickle.dump(data, f)


# ---------------- 时间匹配 ----------------
def find_nearest_by_time(item_list, target_t_ms):
    """列表里挑 t_ms 最接近目标的一条；元素需含 t_ms 字段。"""
    if not item_list:
        return None
    best_idx, best_dt = 0, 1e18
    for i, item in enumerate(item_list):
        dt = abs(item["t_ms"] - target_t_ms)
        if dt < best_dt:
            best_dt, best_idx = dt, i
    return item_list[best_idx]


def find_nearest_frame(frames, target_t_ms):
    """返回 (帧, 时间差ms)；雷达/相机通用。"""
    if not frames:
        return None, 1e18
    nearest = find_nearest_by_time(frames, target_t_ms)
    return nearest, abs(nearest["t_ms"] - target_t_ms)


def build_gt_match_map(radar_frames, gt_list, max_diff_ms):
    """全局一对一 GT 匹配：每个 GT 只分配给时间最近的雷达帧。"""
    radar_times = np.array([f["t_ms"] for f in radar_frames])
    match_map = [None] * len(radar_frames)
    match_dt = [1e18] * len(radar_frames)
    for gt_item in gt_list:
        diffs = np.abs(radar_times - gt_item["t_ms"])
        idx = int(np.argmin(diffs))
        dt = diffs[idx]
        if dt > max_diff_ms or dt >= match_dt[idx]:
            continue
        match_map[idx] = gt_item
        match_dt[idx] = dt
    return match_map


# ---------------- odom ----------------
def load_odom_list(bag_path, odom_topic):
    import rosbag
    odom_list = []
    with rosbag.Bag(bag_path, "r") as bag:
        for _, msg, t in bag.read_messages(topics=[odom_topic]):
            odom_list.append({
                "t_ms": int(round(t.to_sec() * 1000)),
                "T": odom_pose_to_matrix(msg),
            })
    return odom_list


def load_odom_list_cached(bag_path, odom_topic):
    cached = _load_cached_topic(bag_path, odom_topic)
    if cached is not None:
        print(f"  ✅ 从缓存加载 {odom_topic}")
        return cached
    print(f"  ⏳ 从 bag 读取 {odom_topic}")
    data = load_odom_list(bag_path, odom_topic)
    _save_cached_topic(bag_path, odom_topic, data)
    return data


# ---------------- GT / Pred ----------------
def load_gt_json_dir(gt_dir):
    """读取 GT JSON 目录，按 t_ms 升序返回 [{"t_ms", "data", ...}]。"""
    import json
    gt_list = []
    if not os.path.isdir(gt_dir):
        print(f"⚠️ GT 目录不存在: {gt_dir}")
        return gt_list
    for fname in sorted(os.listdir(gt_dir)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(gt_dir, fname), "r") as f:
            data = json.load(f)
        if "timestamp" not in data:
            continue
        t_raw = data["timestamp"]
        if t_raw > 1e18:
            t_ms = t_raw // 1_000_000
        elif t_raw > 1e12:
            t_ms = t_raw
        else:
            t_ms = int(round(t_raw * 1000))
        gt_list.append({
            "t_ms": t_ms,
            "frame_token": data.get("C_FrameID", fname),
            "data": data,
            "fname": fname,
        })
    gt_list.sort(key=lambda x: x["t_ms"])
    return gt_list


def load_pred_csv(pred_csv_path):
    """读取 Pred CSV（按 lidar_ts 聚合成帧），按 t_ms 升序返回。"""
    import csv
    if not os.path.exists(pred_csv_path):
        print(f"⚠️ Pred CSV 不存在: {pred_csv_path}")
        return []
    pred_dict = {}
    with open(pred_csv_path, "r") as f:
        for row in csv.DictReader(f):
            t_ms = int(row["lidar_ts"])
            slot = pred_dict.setdefault(t_ms, {"t_ms": t_ms, "objects": []})
            slot["objects"].append({
                "track_id": int(row["track_id"]),
                "category": row["cls"],
                "translation": [float(row["x"]), float(row["y"]), float(row["z"])],
                "size": [float(row["w"]), float(row["l"]), float(row["h"])],
                "yaw": float(row["yaw"]),
                "vx": float(row["vx"]),
                "vy": float(row["vy"]),
                "conf": float(row["conf"]),
                "attribute": row["attribute"],
            })
    return sorted(pred_dict.values(), key=lambda x: x["t_ms"])
