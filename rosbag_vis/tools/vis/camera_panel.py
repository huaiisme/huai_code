"""右侧纵向三相机面板（FRONT / LEFT FRONT / RIGHT FRONT）。"""
import numpy as np

from utils.image import fit_image_fill_width, draw_label
from tools.bag_reader.base import find_nearest_frame

_CAMERA_ORDER = [
    ("front", "FRONT"),
    ("front_left", "LEFT FRONT"),
    ("front_right", "RIGHT FRONT"),
]


def build_camera_panel(cam_data, t_ms, max_diff_ms, panel_w, gap=0):
    """按宽度撑满每路相机图并纵向拼接，返回 BGR ndarray。"""
    img_list, total_h = [], 0
    for name, label in _CAMERA_ORDER:
        frame, _ = find_nearest_frame(cam_data[name], t_ms)
        if frame is not None and abs(frame["t_ms"] - t_ms) <= max_diff_ms:
            img = fit_image_fill_width(frame["image"].copy(), panel_w)
        else:
            img = np.zeros((120, panel_w, 3), dtype=np.uint8)
        img = draw_label(img, label)
        img_list.append(img)
        total_h += img.shape[0]
    total_h += gap * (len(img_list) - 1)

    canvas = np.zeros((total_h, panel_w, 3), dtype=np.uint8)
    y = 0
    for img in img_list:
        canvas[y:y + img.shape[0], 0:panel_w] = img
        y += img.shape[0] + gap
    return canvas
