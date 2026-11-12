"""OpenCV / matplotlib 图像工具：画布互转、缩放、面板标签。"""
import cv2
import numpy as np


def fig_to_cv2(fig):
    """matplotlib 画布 → OpenCV BGR 图像。"""
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()
    buf = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8).reshape(h, w, 3)
    return cv2.cvtColor(buf, cv2.COLOR_RGB2BGR)


def resize_to_height(img, target_h):
    """等比例缩放到指定高度。"""
    h = img.shape[0]
    if h == target_h:
        return img
    scale = target_h / h
    return cv2.resize(img, (int(img.shape[1] * scale), target_h), interpolation=cv2.INTER_AREA)


def fit_image_fill_width(img, panel_w):
    """按面板宽度撑满，高度自适应。"""
    h, w = img.shape[:2]
    scale = panel_w / w
    return cv2.resize(img, (panel_w, int(h * scale)), interpolation=cv2.INTER_AREA)


def draw_label(img, text):
    """左上角叠加半透明黑底白字标签。"""
    overlay = img.copy()
    cv2.rectangle(overlay, (10, 10), (170, 38), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)
    cv2.putText(img, text, (18, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (255, 255, 255), 2, cv2.LINE_AA)
    return img
