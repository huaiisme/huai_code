import numpy as np
import cv2
from nuscenes.nuscenes import NuScenes
from pyquaternion import Quaternion

# ========== 配置项 ==========
NUSCENES_ROOT = "/mnt/Ddisk/data/nuscenes"
VERSION = "v1.0-mini"
SAMPLE_IDX = 0
CAM_NAME = "CAM_FRONT"
POINT_RADIUS = 3
MAX_DEPTH = 80.0
# ============================

def get_sensor_extrinsic(nusc, sample_data_token):
    """获取传感器到自车的外参变换矩阵 + 相机内参"""
    sd_record = nusc.get("sample_data", sample_data_token)
    cs_record = nusc.get("calibrated_sensor", sd_record["calibrated_sensor_token"])

    # 传感器坐标系 -> 自车坐标系
    rot = Quaternion(cs_record["rotation"]).rotation_matrix
    trans = np.array(cs_record["translation"])
    T_sensor2ego = np.eye(4)
    T_sensor2ego[:3, :3] = rot
    T_sensor2ego[:3, 3] = trans

    K = np.array(cs_record["camera_intrinsic"])
    return T_sensor2ego, K


def main():
    nusc = NuScenes(version=VERSION, dataroot=NUSCENES_ROOT, verbose=True)
    sample = nusc.sample[SAMPLE_IDX]

    cam_token = sample["data"][CAM_NAME]
    lidar_token = sample["data"]["LIDAR_TOP"]
    cam_path = nusc.get_sample_data_path(cam_token)
    lidar_path = nusc.get_sample_data_path(lidar_token)

    img = cv2.imread(cam_path)
    img_h, img_w = img.shape[:2]
    print(f"图像尺寸: {img_w} x {img_h}")

    # 读取点云 xyz
    points = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 5)[:, :3]
    print(f"原始点云总数: {len(points)}")

    # 获取外参和内参
    T_lidar2ego, _ = get_sensor_extrinsic(nusc, lidar_token)
    T_cam2ego, K = get_sensor_extrinsic(nusc, cam_token)

    # ========== 核心修复：直接在自车系下计算相对变换 ==========
    # 激光雷达点 -> 自车系 -> 相机系
    # 公式: P_cam = inv(T_cam2ego) @ T_lidar2ego @ P_lidar
    T_lidar2cam = np.linalg.inv(T_cam2ego) @ T_lidar2ego

    # 齐次坐标变换
    points_homo = np.hstack([points, np.ones((len(points), 1))])
    points_cam = (T_lidar2cam @ points_homo.T).T[:, :3]

    print(f"相机系z(深度)范围: {points_cam[:,2].min():.2f} ~ {points_cam[:,2].max():.2f} 米")

    # 筛选：相机前方 + 最大深度内
    mask = (points_cam[:, 2] > 0) & (points_cam[:, 2] < MAX_DEPTH)
    print(f"相机前方且<{MAX_DEPTH}米的点数: {np.sum(mask)}")

    if np.sum(mask) == 0:
        print("❌ 无有效点")
        return

    points_cam = points_cam[mask]

    # 投影到像素平面
    pixels = (K @ points_cam.T).T
    pixels = pixels[:, :2] / pixels[:, 2:3]

    # 筛选图像范围内
    mask_in = (pixels[:, 0] >= 0) & (pixels[:, 0] < img_w) & \
              (pixels[:, 1] >= 0) & (pixels[:, 1] < img_h)
    print(f"落在图像内的点数: {np.sum(mask_in)}")

    pixels_in = pixels[mask_in].astype(int)
    depth_in = points_cam[mask_in, 2]

    # 深度着色
    depth_norm = np.clip(depth_in / MAX_DEPTH * 255, 0, 255).astype(np.uint8)
    color_map = cv2.applyColorMap(depth_norm.reshape(-1, 1), cv2.COLORMAP_JET).reshape(-1, 3)

    for u, v, color in zip(pixels_in[:, 0], pixels_in[:, 1], color_map):
        cv2.circle(img, (int(u), int(v)), POINT_RADIUS, color.tolist(), -1)

    cv2.putText(img, "Red=Near  Blue=Far", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

    cv2.imwrite("lidar_proj_fixed.jpg", img)
    print("\n✅ 投影图已保存为 lidar_proj_fixed.jpg")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()
