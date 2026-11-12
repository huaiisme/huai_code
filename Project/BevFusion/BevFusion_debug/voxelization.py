import numpy as np
import torch
from nuscenes.nuscenes import NuScenes
from pyquaternion import Quaternion
import cv2

# ========== 沿用之前的统一配置，保证坐标系完全对齐 ==========
BEV_RANGE = [-50.0, -50.0, 50.0, 50.0]  # x_min, y_min, x_max, y_max
Z_RANGE = [-5.0, 3.0]                    # z_min, z_max
VOXEL_SIZE = [0.5, 0.5, 0.2]             # x, y, z 方向的体素大小（米）

# 计算体素网格尺寸
VOXEL_X_NUM = int((BEV_RANGE[2] - BEV_RANGE[0]) / VOXEL_SIZE[0])
VOXEL_Y_NUM = int((BEV_RANGE[3] - BEV_RANGE[1]) / VOXEL_SIZE[1])
VOXEL_Z_NUM = int((Z_RANGE[1] - Z_RANGE[0]) / VOXEL_SIZE[2])

NUSCENES_ROOT = "/mnt/Ddisk/data/nuscenes"
VERSION = "v1.0-mini"
SAMPLE_IDX = 0


def get_lidar_points_in_ego(nusc, sample):
    """获取自车坐标系下的点云 (x, y, z, intensity)"""
    lidar_token = sample["data"]["LIDAR_TOP"]
    lidar_path = nusc.get_sample_data_path(lidar_token)
    
    sd_record = nusc.get("sample_data", lidar_token)
    cs_record = nusc.get("calibrated_sensor", sd_record["calibrated_sensor_token"])

    points = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 5)
    points_xyz = points[:, :3]
    points_intensity = points[:, 3:4]

    rot = Quaternion(cs_record["rotation"]).rotation_matrix
    trans = np.array(cs_record["translation"])
    points_xyz_ego = (rot @ points_xyz.T).T + trans
    
    return np.hstack([points_xyz_ego, points_intensity])  # [N, 4] x,y,z,intensity


def voxelize_numpy(points):
    """
    numpy 版体素化，便于理解原理
    输入: points [N, 4]  x,y,z,intensity
    输出:
        voxels: [M, 4] 每个体素的聚合特征（均值x,y,z + 均值强度）
        voxel_coords: [M, 3] 每个体素的网格索引 (z_idx, y_idx, x_idx)
        voxel_num_points: [M] 每个体素内的点数量
    """
    # 1. 范围过滤
    mask = (points[:, 0] >= BEV_RANGE[0]) & (points[:, 0] < BEV_RANGE[2]) & \
           (points[:, 1] >= BEV_RANGE[1]) & (points[:, 1] < BEV_RANGE[3]) & \
           (points[:, 2] >= Z_RANGE[0]) & (points[:, 2] < Z_RANGE[1])
    points = points[mask]
    
    if len(points) == 0:
        return np.zeros((0,4)), np.zeros((0,3), dtype=np.int32), np.zeros(0, dtype=np.int32)

    # 2. 计算每个点对应的体素索引
    x_idx = np.floor((points[:, 0] - BEV_RANGE[0]) / VOXEL_SIZE[0]).astype(np.int32)
    y_idx = np.floor((points[:, 1] - BEV_RANGE[1]) / VOXEL_SIZE[1]).astype(np.int32)
    z_idx = np.floor((points[:, 2] - Z_RANGE[0]) / VOXEL_SIZE[2]).astype(np.int32)
    
    # 体素唯一键：用 z*y_num*x_num + y*x_num + x 做唯一标识
    voxel_keys = z_idx * VOXEL_Y_NUM * VOXEL_X_NUM + y_idx * VOXEL_X_NUM + x_idx

    # 3. 按体素分组，聚合特征
    # 排序，相同体素的点排在一起
    sorted_indices = np.argsort(voxel_keys)
    sorted_keys = voxel_keys[sorted_indices]
    sorted_points = points[sorted_indices]
    
    # 找到每个体素的边界
    unique_keys, counts = np.unique(sorted_keys, return_counts=True)
    voxel_num_points = counts
    
    # 计算每个体素的特征均值
    voxels = np.zeros((len(unique_keys), 4), dtype=np.float32)
    voxel_coords = np.zeros((len(unique_keys), 3), dtype=np.int32)
    
    start = 0
    for i, cnt in enumerate(counts):
        end = start + cnt
        voxels[i] = np.mean(sorted_points[start:end], axis=0)
        # 反解 z,y,x 索引
        key = unique_keys[i]
        z = key // (VOXEL_Y_NUM * VOXEL_X_NUM)
        rem = key % (VOXEL_Y_NUM * VOXEL_X_NUM)
        y = rem // VOXEL_X_NUM
        x = rem % VOXEL_X_NUM
        voxel_coords[i] = [z, y, x]
        start = end
    
    return voxels, voxel_coords, voxel_num_points


def visualize_voxel_bev(voxels, voxel_coords, save_path="voxel_bev.jpg"):
    """把体素投影到BEV平面可视化，验证空间对齐"""
    bev_img = np.zeros((VOXEL_Y_NUM, VOXEL_X_NUM, 3), dtype=np.uint8)
    
    for i in range(len(voxels)):
        z_idx, y_idx, x_idx = voxel_coords[i]
        # 按高度着色
        z_val = z_idx * VOXEL_SIZE[2] + Z_RANGE[0]
        color = int(np.clip((z_val + 5) / 8 * 255, 0, 255))
        bev_img[y_idx, x_idx] = [color, 200, 255 - color]
    
    # 上下翻转，和之前BEV可视化方向一致
    bev_img = cv2.flip(bev_img, 0)
    cv2.imwrite(save_path, bev_img)
    print(f"✅ 体素BEV可视化已保存到 {save_path}")


def main():
    nusc = NuScenes(version=VERSION, dataroot=NUSCENES_ROOT, verbose=True)
    sample = nusc.sample[SAMPLE_IDX]

    # 1. 获取自车系点云
    points = get_lidar_points_in_ego(nusc, sample)
    print(f"原始点云数量: {len(points)}")

    # 2. 体素化
    voxels, voxel_coords, voxel_num_points = voxelize_numpy(points)
    
    print(f"\n===== 体素化结果 =====")
    print(f"体素总数量: {len(voxels)}")
    print(f"体素网格尺寸: {VOXEL_Z_NUM} x {VOXEL_Y_NUM} x {VOXEL_X_NUM} (Z x Y x X)")
    print(f"单个体素内最多点数: {voxel_num_points.max()}")
    print(f"单个体素内平均点数: {voxel_num_points.mean():.2f}")
    print(f"体素特征维度: {voxels.shape[1]}")

    # 3. 可视化验证
    visualize_voxel_bev(voxels, voxel_coords)


if __name__ == "__main__":
    main()
