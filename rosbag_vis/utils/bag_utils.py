import numpy as np
import rosbag
import sensor_msgs.point_cloud2 as pc2
import os
import json
import csv
import pickle


def get_cache_path(bag_path):
    """缓存文件放在 bag 同目录下，隐藏文件形式"""
    bag_abs = os.path.abspath(bag_path)
    bag_dir = os.path.dirname(bag_abs)
    bag_name = os.path.basename(bag_abs).replace(".bag", "")
    return os.path.join(bag_dir, f".{bag_name}_cache.pkl")


def load_lidar_frames_cached(bag_path, lidar_topic):
    """带缓存的雷达读取"""
    cache_file = get_cache_path(bag_path)
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            all_cache = pickle.load(f)
        if lidar_topic in all_cache:
            print(f"  ✅ 从缓存加载 {lidar_topic}")
            return all_cache[lidar_topic]

    print(f"  ⏳ 从bag读取 {lidar_topic}")
    frames = load_lidar_frames(bag_path, lidar_topic)

    all_cache = {}
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            all_cache = pickle.load(f)
    all_cache[lidar_topic] = frames
    with open(cache_file, 'wb') as f:
        pickle.dump(all_cache, f)
    return frames


def load_odom_list_cached(bag_path, odom_topic):
    """带缓存的odom读取"""
    cache_file = get_cache_path(bag_path)
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            all_cache = pickle.load(f)
        if odom_topic in all_cache:
            print(f"  ✅ 从缓存加载 {odom_topic}")
            return all_cache[odom_topic]

    print(f"  ⏳ 从bag读取 {odom_topic}")
    odom_list = load_odom_list(bag_path, odom_topic)

    all_cache = {}
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            all_cache = pickle.load(f)
    all_cache[odom_topic] = odom_list
    with open(cache_file, 'wb') as f:
        pickle.dump(all_cache, f)
    return odom_list


def load_odom_list(bag_path, odom_topic):
    from .tf_utils import odom_pose_to_matrix
    odom_list = []
    with rosbag.Bag(bag_path, 'r') as bag:
        for topic, msg, t in bag.read_messages(topics=[odom_topic]):
            odom_list.append({
                "t_ms": int(round(t.to_sec() * 1000)),
                "T": odom_pose_to_matrix(msg)
            })
    return odom_list


def load_lidar_frames(bag_path, lidar_topic):
    frames = []
    with rosbag.Bag(bag_path, 'r') as bag:
        for topic, msg, t in bag.read_messages(topics=[lidar_topic]):
            pts = list(pc2.read_points(msg, field_names=["x", "y", "z"], skip_nans=True))
            if len(pts) > 0:
                frames.append({
                    "t_ms": int(round(t.to_sec() * 1000)),
                    "pts": np.array(pts, dtype=np.float32)
                })
    return frames


# ========== 时间匹配（统一底层实现） ==========
def find_nearest_by_time(item_list, target_t_ms):
    """通用时间最近邻匹配：返回匹配到的条目"""
    if len(item_list) == 0:
        return None
    best_idx, best_dt = 0, 1e18
    for i, item in enumerate(item_list):
        dt = abs(item["t_ms"] - target_t_ms)
        if dt < best_dt:
            best_dt, best_idx = dt, i
    return item_list[best_idx]


def find_nearest_frame(frames, target_t_ms):
    """雷达帧专用匹配：返回 (帧数据, 时间差)"""
    if len(frames) == 0:
        return None, 1e18
    nearest = find_nearest_by_time(frames, target_t_ms)
    dt = abs(nearest["t_ms"] - target_t_ms)
    return nearest, dt


def build_gt_match_map(radar_frames, gt_list, max_diff_ms):
    """全局一对一GT匹配：每个GT只分配给时间最接近的雷达帧
    返回：长度等于雷达帧数的匹配表，每帧对应一个GT或None
    """
    radar_times = np.array([f["t_ms"] for f in radar_frames])
    match_map = [None] * len(radar_frames)
    match_dt = [1e18] * len(radar_frames)

    for gt_item in gt_list:
        gt_t = gt_item["t_ms"]
        diffs = np.abs(radar_times - gt_t)
        nearest_idx = int(np.argmin(diffs))
        dt = diffs[nearest_idx]

        if dt > max_diff_ms:
            continue
        if dt < match_dt[nearest_idx]:
            match_map[nearest_idx] = gt_item
            match_dt[nearest_idx] = dt
    return match_map


# ========== GT / Pred 数据加载 ==========
def load_gt_json_dir(gt_dir):
    gt_list = []
    if not os.path.exists(gt_dir):
        print(f"⚠️ GT目录不存在: {gt_dir}")
        return gt_list
    for fname in os.listdir(gt_dir):
        if not fname.endswith(".json"):
            continue
        json_path = os.path.join(gt_dir, fname)
        with open(json_path, 'r') as f:
            data = json.load(f)
        if "timestamp" not in data:
            continue
        t_raw = data["timestamp"]
        if t_raw > 1e18:
            t_ms = t_raw // 1000000
        elif t_raw > 1e12:
            t_ms = t_raw
        else:
            t_ms = int(round(t_raw * 1000))
        gt_list.append({
            "t_ms": t_ms,
            "frame_token": data.get("C_FrameID", fname),
            "data": data,
            "fname": fname
        })
    gt_list.sort(key=lambda x: x["t_ms"])
    return gt_list


def load_pred_csv(pred_csv_path):
    if not os.path.exists(pred_csv_path):
        print(f"⚠️ Pred CSV不存在: {pred_csv_path}")
        return []
    pred_dict = {}
    with open(pred_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            t_ms = int(row["lidar_ts"])
            if t_ms not in pred_dict:
                pred_dict[t_ms] = {"t_ms": t_ms, "objects": []}
            pred_dict[t_ms]["objects"].append({
                "track_id": int(row["track_id"]),
                "category": row["cls"],
                "translation": [float(row["x"]), float(row["y"]), float(row["z"])],
                "size": [float(row["w"]), float(row["l"]), float(row["h"])],
                "yaw": float(row["yaw"]),
                "vx": float(row["vx"]),
                "vy": float(row["vy"]),
                "conf": float(row["conf"]),
                "attribute": row["attribute"]
            })
    return sorted(pred_dict.values(), key=lambda x: x["t_ms"])
