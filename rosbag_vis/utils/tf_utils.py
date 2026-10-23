import numpy as np
from scipy.spatial.transform import Rotation


def create_tf_matrix(xyz, rpy):
    T = np.eye(4)
    T[:3, 3] = np.array(xyz)
    T[:3, :3] = Rotation.from_euler("xyz", rpy).as_matrix()
    return T


def odom_pose_to_matrix(odom_msg):
    p = odom_msg.pose.pose.position
    q = odom_msg.pose.pose.orientation
    T = np.eye(4)
    T[:3, 3] = [p.x, p.y, p.z]
    T[:3, :3] = Rotation.from_quat([q.x, q.y, q.z, q.w]).as_matrix()
    return T


def get_yaw_from_matrix(T):
    return Rotation.from_matrix(T[:3, :3]).as_euler("xyz")[2]


def transform_points(points, T):
    N = points.shape[0]
    homo = np.hstack([points, np.ones((N, 1))])
    return (T @ homo.T).T[:, :3]


# ========== 坐标系转换（统一3D版本，点云和框通用） ==========
def world_to_ego_view(pts_world, car_x, car_y, yaw):
    """兼容旧2D接口：仅XY平面转换"""
    pts_rel = pts_world.copy()
    pts_rel[:, 0] -= car_x
    pts_rel[:, 1] -= car_y
    cos_yaw, sin_yaw = np.cos(-yaw), np.sin(-yaw)
    x_new = pts_rel[:, 0] * cos_yaw - pts_rel[:, 1] * sin_yaw
    y_new = pts_rel[:, 0] * sin_yaw + pts_rel[:, 1] * cos_yaw
    pts_rel[:, 0], pts_rel[:, 1] = x_new, y_new
    return pts_rel


def world_to_ego_view_3d(pts_world, car_x, car_y, car_z, car_yaw):
    """3D完整版：世界系 → 自车系（XY旋转平移，Z平移）
    点云和框中心点共用此函数，保证变换完全一致
    """
    dx = pts_world[:, 0] - car_x
    dy = pts_world[:, 1] - car_y
    cos_yaw = np.cos(-car_yaw)
    sin_yaw = np.sin(-car_yaw)

    x = dx * cos_yaw - dy * sin_yaw
    y = dx * sin_yaw + dy * cos_yaw
    z = pts_world[:, 2] - car_z

    return np.column_stack([x, y, z])


# ========== GT/框 坐标转换（全部复用点云同款矩阵变换） ==========
def gt_quat_to_yaw(rot_list):
    """GT四元数转yaw，格式 [qw, qx, qy, qz]"""
    qw, qx, qy, qz = rot_list
    return Rotation.from_quat([qx, qy, qz, qw]).as_euler("xyz")[2]


def box_ego_to_world(ego_x, ego_y, ego_z, ego_yaw, odom_T):
    """框：自车系 → 世界系，复用 transform_points 保证和点云严格对齐"""
    center_ego = np.array([[ego_x, ego_y, ego_z]])
    center_world = transform_points(center_ego, odom_T)
    world_yaw = ego_yaw + get_yaw_from_matrix(odom_T)
    return center_world[0, 0], center_world[0, 1], center_world[0, 2], world_yaw


def box_world_to_ego_view(world_x, world_y, world_z, world_yaw, car_x, car_y, car_z, car_yaw):
    """框：世界系 → 自车视角，复用 world_to_ego_view_3d 保证和点云严格对齐"""
    center_world = np.array([[world_x, world_y, world_z]])
    center_view = world_to_ego_view_3d(center_world, car_x, car_y, car_z, car_yaw)
    view_yaw = world_yaw - car_yaw
    return center_view[0, 0], center_view[0, 1], center_view[0, 2], view_yaw


# 保留旧接口兼容BEV脚本
def gt_ego_to_world(obj_translation, obj_yaw_ego, odom_T):
    world_x, world_y, _, world_yaw = box_ego_to_world(
        obj_translation[0], obj_translation[1], obj_translation[2], obj_yaw_ego, odom_T
    )
    return world_x, world_y, world_yaw


def gt_world_to_ego_view(world_x, world_y, world_yaw, car_x, car_y, car_yaw):
    view_x, view_y, _, view_yaw = box_world_to_ego_view(
        world_x, world_y, 0, world_yaw, car_x, car_y, 0, car_yaw
    )
    return view_x, view_y, view_yaw
