"""坐标系语义：世界系 ↔ 自车视角，以及 3D 框的两端变换。

点云变换链路（与逐帧渲染完全一致）：
    lidar 系 --T_lidar--> 自车系 --odom_T--> 世界系 --world_to_ego_view_*--> 自车视角

GT 框在自车系给出，Pred 框在世界系给出，二者都统一转到自车视角后再绘制。
"""
import numpy as np

from utils.tf import get_yaw_from_matrix, transform_points


def world_to_ego_view_2d(pts_world, car_x, car_y, car_yaw):
    """世界系 → 自车视角（仅 XY 平面旋转平移，Z 保持不变，用于 BEV）。"""
    pts = np.asarray(pts_world, dtype=float).copy()
    pts[:, 0] -= car_x
    pts[:, 1] -= car_y
    c, s = np.cos(-car_yaw), np.sin(-car_yaw)
    x_new = pts[:, 0] * c - pts[:, 1] * s
    y_new = pts[:, 0] * s + pts[:, 1] * c
    pts[:, 0], pts[:, 1] = x_new, y_new
    return pts


def world_to_ego_view_3d(pts_world, car_x, car_y, car_z, car_yaw):
    """世界系 → 自车视角（XYZ 全部对齐自车原点，用于 3D 视图）。"""
    pts = world_to_ego_view_2d(pts_world, car_x, car_y, car_yaw)
    pts[:, 2] -= car_z
    return pts


def box_ego_to_world(ego_x, ego_y, ego_z, ego_yaw, odom_T):
    """框中心：自车系 → 世界系。返回 (wx, wy, wz, world_yaw)。"""
    center = transform_points(np.array([[ego_x, ego_y, ego_z]], dtype=float), odom_T)
    world_yaw = ego_yaw + get_yaw_from_matrix(odom_T)
    return float(center[0, 0]), float(center[0, 1]), float(center[0, 2]), float(world_yaw)


def box_world_to_ego_view(wx, wy, wz, world_yaw, car_x, car_y, car_z, car_yaw):
    """框中心：世界系 → 自车视角。返回 (vx, vy, vz, view_yaw)。"""
    center = world_to_ego_view_3d(
        np.array([[wx, wy, wz]], dtype=float), car_x, car_y, car_z, car_yaw)
    view_yaw = world_yaw - car_yaw
    return float(center[0, 0]), float(center[0, 1]), float(center[0, 2]), float(view_yaw)


# ---- 2D BEV 专用薄封装（z 不参与绘制，调用方自行保留原始 z） ----
def gt_ego_to_world(ego_x, ego_y, ego_yaw, odom_T):
    wx, wy, _, world_yaw = box_ego_to_world(ego_x, ego_y, 0.0, ego_yaw, odom_T)
    return wx, wy, world_yaw


def gt_world_to_ego_view(wx, wy, world_yaw, car_x, car_y, car_yaw):
    vx, vy, _, view_yaw = box_world_to_ego_view(wx, wy, 0.0, world_yaw,
                                                car_x, car_y, 0.0, car_yaw)
    return vx, vy, view_yaw
