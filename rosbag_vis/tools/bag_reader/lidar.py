"""雷达点云读取（带缓存）。"""
import numpy as np

from tools.bag_reader.base import _load_cached_topic, _save_cached_topic


def load_lidar_frames(bag_path, lidar_topic):
    """读取 bag 中全部雷达帧：[{"t_ms", "pts": Nx3 float32}]。"""
    import rosbag
    import sensor_msgs.point_cloud2 as pc2

    frames = []
    with rosbag.Bag(bag_path, "r") as bag:
        for _, msg, t in bag.read_messages(topics=[lidar_topic]):
            pts = list(pc2.read_points(msg, field_names=["x", "y", "z"], skip_nans=True))
            if pts:
                frames.append({
                    "t_ms": int(round(t.to_sec() * 1000)),
                    "pts": np.array(pts, dtype=np.float32),
                })
    return frames


def load_lidar_frames_cached(bag_path, lidar_topic):
    cached = _load_cached_topic(bag_path, lidar_topic)
    if cached is not None:
        print(f"  ✅ 从缓存加载 {lidar_topic}")
        return cached
    print(f"  ⏳ 从 bag 读取 {lidar_topic}")
    frames = load_lidar_frames(bag_path, lidar_topic)
    _save_cached_topic(bag_path, lidar_topic, frames)
    return frames
