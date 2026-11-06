"""坐标变换矩阵与旋转角工具。

只负责 4x4 齐次变换矩阵的构造/解析，不涉及坐标系语义。
"""
import numpy as np
from scipy.spatial.transform import Rotation


def create_tf_matrix(xyz, rpy):
    """由平移 (x,y,z) 和欧拉角 (roll,pitch,yaw, 内旋 xyz) 构造 4x4 变换矩阵。"""
    T = np.eye(4)
    T[:3, 3] = np.asarray(xyz, dtype=float)
    T[:3, :3] = Rotation.from_euler("xyz", rpy).as_matrix()
    return T


def odom_pose_to_matrix(odom_msg):
    """nav_msgs/Odometry 消息 → 4x4 变换矩阵。"""
    p = odom_msg.pose.pose.position
    q = odom_msg.pose.pose.orientation
    T = np.eye(4)
    T[:3, 3] = [p.x, p.y, p.z]
    T[:3, :3] = Rotation.from_quat([q.x, q.y, q.z, q.w]).as_matrix()
    return T


def get_yaw_from_matrix(T):
    """取变换矩阵在 z 轴上的偏航角（弧度）。"""
    return float(Rotation.from_matrix(np.asarray(T)[:3, :3]).as_euler("xyz")[2])


def transform_points(points, T):
    """齐次坐标变换：Nx3 点云 × 4x4 矩阵 → Nx3 点云。"""
    points = np.asarray(points, dtype=float)
    n = points.shape[0]
    homo = np.hstack([points, np.ones((n, 1))])
    return (np.asarray(T) @ homo.T).T[:, :3]


def gt_quat_to_yaw(rot_list):
    """GT JSON 里的四元数 [qw, qx, qy, qz] → yaw 角（弧度）。"""
    qw, qx, qy, qz = rot_list
    return float(Rotation.from_quat([qx, qy, qz, qw]).as_euler("xyz")[2])
