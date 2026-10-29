"""右侧纵向三相机面板（FRONT / LEFT FRONT / RIGHT FRONT）。

面板输出尺寸固定为 (panel_h, panel_w, 3)，不随某路相机是否命中时间戳而抖动，
避免下游 hstack / 写视频时出现 "All images in a movie should have same size"。
"""
import cv2
import numpy as np

from utils.image import fit_image_fill_width, draw_label
from tools.bag_reader.base import find_nearest_frame

_CAMERA_ORDER = [
    ("front", "FRONT"),
    ("front_left", "LEFT FRONT"),
    ("front_right", "RIGHT FRONT"),
]


def build_camera_panel(cam_data, t_ms, max_diff_ms, panel_w, panel_h=900, gap=0):
    """三路相机纵向拼接，返回固定 (panel_h, panel_w, 3) BGR ndarray。

    每路相机强制缩放到 panel_h/3 高（宽度撑满 panel_w）；缺帧时填黑底占位，
    尺寸与命中帧完全一致。
    """
    n = len(_CAMERA_ORDER)
    single_h = (panel_h - gap * (n - 1)) // n
    img_list = []
    for name, label in _CAMERA_ORDER:
        frame, _ = find_nearest_frame(cam_data[name], t_ms)
        if frame is not None and abs(frame["t_ms"] - t_ms) <= max_diff_ms:
            img = fit_image_fill_width(frame["image"].copy(), panel_w)
        else:
            img = np.zeros((single_h, panel_w, 3), dtype=np.uint8)
        if img.shape[0] != single_h:
            img = cv2.resize(img, (panel_w, single_h), interpolation=cv2.INTER_AREA)
        img = draw_label(img, label)
        img_list.append(img)

    canvas = np.zeros((single_h * n + gap * (n - 1), panel_w, 3), dtype=np.uint8)
    y = 0
    for img in img_list:
        canvas[y:y + single_h, 0:panel_w] = img
        y += single_h + gap
    return canvas
