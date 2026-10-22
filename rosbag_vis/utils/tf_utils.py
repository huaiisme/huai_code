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


def world_to_ego_view(pts_world, car_x, car_y, yaw):
    pts_rel = pts_world.copy()
    pts_rel[:, 0] -= car_x
    pts_rel[:, 1] -= car_y
    cos_yaw, sin_yaw = np.cos(-yaw), np.sin(-yaw)
    x_new = pts_rel[:, 0] * cos_yaw - pts_rel[:, 1] * sin_yaw
    y_new = pts_rel[:, 0] * sin_yaw + pts_rel[:, 1] * cos_yaw
    pts_rel[:, 0], pts_rel[:, 1] = x_new, y_new
    return pts_rel


# ========== GT相关 ==========
def gt_quat_to_yaw(rot_list):
    """GT四元数转yaw，格式 [qw, qx, qy, qz]"""
    qw, qx, qy, qz = rot_list
    return Rotation.from_quat([qx, qy, qz, qw]).as_euler("xyz")[2]


def gt_ego_to_world(obj_translation, obj_yaw_ego, odom_T):
    """GT物体从ego坐标系转到世界坐标系"""
    pts_ego = np.array([obj_translation])
    pts_world = transform_points(pts_ego, odom_T)
    car_yaw = get_yaw_from_matrix(odom_T)
    return pts_world[0, 0], pts_world[0, 1], obj_yaw_ego + car_yaw


def gt_world_to_ego_view(world_x, world_y, world_yaw, car_x, car_y, car_yaw):
    """GT物体从世界坐标系转到自车视角"""
    pts_world = np.array([[world_x, world_y, 0]])
    pts_view = world_to_ego_view(pts_world, car_x, car_y, car_yaw)
    return pts_view[0, 0], pts_view[0, 1], world_yaw - car_yaw
