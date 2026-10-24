"""相机图像读取（带缓存，BGR8）。"""
from tools.bag_reader.base import _load_cached_topic, _save_cached_topic

_bridge = None


def _get_bridge():
    global _bridge
    if _bridge is None:
        from cv_bridge import CvBridge
        _bridge = CvBridge()
    return _bridge


def load_camera_frames(bag_path, camera_topic, encoding="bgr8"):
    """读取 bag 中全部相机帧：[{"t_ms", "image": BGR ndarray}]。解码失败的帧跳过。"""
    import rosbag
    bridge = _get_bridge()
    frames = []
    with rosbag.Bag(bag_path, "r") as bag:
        for _, msg, t in bag.read_messages(topics=[camera_topic]):
            try:
                cv_img = bridge.imgmsg_to_cv2(msg, desired_encoding=encoding)
            except Exception:
                continue
            frames.append({
                "t_ms": int(round(t.to_sec() * 1000)),
                "image": cv_img,
            })
    return frames


def load_camera_frames_cached(bag_path, camera_topic, encoding="bgr8"):
    cached = _load_cached_topic(bag_path, camera_topic)
    if cached is not None:
        print(f"  ✅ 从缓存加载 {camera_topic}")
        return cached
    print(f"  ⏳ 从 bag 读取 {camera_topic}")
    frames = load_camera_frames(bag_path, camera_topic, encoding)
    _save_cached_topic(bag_path, camera_topic, frames)
    return frames
