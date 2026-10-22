import numpy as np
import rosbag
import sensor_msgs.point_cloud2 as pc2
import os
import json
import csv

def load_odom_list(bag_path, odom_topic):
    """读取bag里所有odom消息，时间戳转成13位毫秒"""
    from .tf_utils import odom_pose_to_matrix

    odom_list = []
    with rosbag.Bag(bag_path, 'r') as bag:
        for topic, msg, t in bag.read_messages(topics=[odom_topic]):
            odom_list.append({
                "t_ms": int(round(t.to_sec() * 1000)),  # 13位毫秒
                "T": odom_pose_to_matrix(msg)
            })
    return odom_list


def load_lidar_frames(bag_path, lidar_topic):
    """读取bag里所有雷达点云帧，时间戳转成13位毫秒"""
    frames = []
    with rosbag.Bag(bag_path, 'r') as bag:
        for topic, msg, t in bag.read_messages(topics=[lidar_topic]):
            pts = list(pc2.read_points(msg, field_names=["x", "y", "z"], skip_nans=True))
            if len(pts) > 0:
                frames.append({
                    "t_ms": int(round(t.to_sec() * 1000)),  # 13位毫秒
                    "pts": np.array(pts, dtype=np.float32)
                })
    return frames


def find_nearest_by_time(item_list, target_t_ms):
    """通用时间最近邻匹配：item_list 每个元素需包含 't_ms' 字段（13位毫秒）"""
    if len(item_list) == 0:
        return None
    best_idx, best_dt = 0, 1e18
    for i, item in enumerate(item_list):
        dt = abs(item["t_ms"] - target_t_ms)
        if dt < best_dt:
            best_dt, best_idx = dt, i
    return item_list[best_idx]

def load_gt_json_dir(gt_dir):
    """读取GT JSON目录下所有文件，时间戳统一成13位毫秒
    """
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
        # 判断位数：19位是纳秒，13位是毫秒
        if t_raw > 1e18:  # 纳秒
            t_ms = t_raw // 1000000
        elif t_raw > 1e12:  # 毫秒（13位）
            t_ms = t_raw
        else:  # 秒
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
    """读取Pred CSV文件
    列：lidar_ts, track_id, cls, x, y, z, w, l, h, yaw, vx, vy, obj_heading, conf, attribute
    返回: [{"t_ms": 毫秒时间戳, "objects": [...]}, ...] 按时间分组
    """
    if not os.path.exists(pred_csv_path):
        print(f"⚠️ Pred CSV不存在: {pred_csv_path}")
        return []

    # 按时间戳分组
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
                "yaw": float(row["yaw"]),  # 已经是弧度
                "vx": float(row["vx"]),
                "vy": float(row["vy"]),
                "conf": float(row["conf"]),
                "attribute": row["attribute"]
            })

    # 转成列表并按时间排序
    pred_list = sorted(pred_dict.values(), key=lambda x: x["t_ms"])
    return pred_list
