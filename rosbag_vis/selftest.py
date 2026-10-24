"""无 bag 的渲染自检：合成点云 + GT/Pred 框，跑通 BEV / 3D 渲染链路。

在装有 numpy/scipy/matplotlib/opencv 的环境下执行：
    python selftest.py
通过则在当前目录生成 selftest_bev.png 和 selftest_3d.png。
"""
import os

import numpy as np

from tools.vis.bev import draw_bev_frame
from tools.vis.lidar_3d import draw_3d_frame


def _synthetic_points():
    """在自车视场上撒两片点云：前向路面 + 一个目标盒附近。"""
    rng = np.random.default_rng(0)
    road = np.column_stack([
        rng.uniform(0, 40, 2000),
        rng.uniform(-15, 15, 2000),
        rng.uniform(-1.5, 0.5, 2000),
    ])
    target = np.column_stack([
        rng.uniform(15, 19, 300),
        rng.uniform(-2, 2, 300),
        rng.uniform(0, 2, 300),
    ])
    return [road.astype(np.float32), target.astype(np.float32)]


def _boxes():
    gt = {"objects": [{
        "ID": 1, "category": "truck",
        "translation": [17.0, 0.0, 1.0], "size": [2.5, 6.0, 2.5], "yaw": 0.1,
    }]}
    pred = {"objects": [{
        "track_id": 7, "category": "truck", "conf": 0.92,
        "translation": [17.3, 0.3, 1.0], "size": [2.4, 5.8, 2.4], "yaw": 0.15,
    }]}
    return gt, pred


def main():
    pts = _synthetic_points()
    gt, pred = _boxes()

    bev_path = os.path.join(os.path.dirname(__file__), "selftest_bev.png")
    n_bev = draw_bev_frame(pts, car_x=100.0, car_y=50.0, yaw=0.1,
                           view_range=50.0, frame_idx=0, t_ms=0,
                           gt_data=gt, pred_data=pred, save_path=bev_path)

    d3_path = os.path.join(os.path.dirname(__file__), "selftest_3d.png")
    n_3d = draw_3d_frame(pts, view_x_back=5.0, view_x_front=45.0, view_y=20.0,
                         view_z_min=-2.0, view_z_max=4.0,
                         gt_data=gt, pred_data=pred, frame_idx=0, t_ms=0,
                         save_path=d3_path)

    assert n_bev > 0 and os.path.exists(bev_path), "BEV 渲染失败"
    assert n_3d > 0 and os.path.exists(d3_path), "3D 渲染失败"
    print(f"✅ BEV  渲染成功: {bev_path}  (点={n_bev})")
    print(f"✅ 3D   渲染成功: {d3_path}  (点={n_3d})")
    print("🎉 2D/3D 渲染链路自检通过")


if __name__ == "__main__":
    main()
