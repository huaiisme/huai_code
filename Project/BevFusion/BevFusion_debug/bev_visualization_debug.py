import numpy as np
import cv2
from nuscenes.nuscenes import NuScenes
from pyquaternion import Quaternion

# ========== BEV 配置（后续模型也用这套参数） ==========
BEV_RANGE = [-50.0, -50.0, 50.0, 50.0]  # [x_min, y_min, x_max, y_max] 单位：米
BEV_RESOLUTION = 0.1  # 每个BEV像素对应0.5米
# 计算BEV图像尺寸
BEV_W = int((BEV_RANGE[2] - BEV_RANGE[0]) / BEV_RESOLUTION)
BEV_H = int((BEV_RANGE[3] - BEV_RANGE[1]) / BEV_RESOLUTION)

# ========== 数据集配置 ==========
NUSCENES_ROOT = "/mnt/Ddisk/data/nuscenes"
VERSION = "v1.0-mini"
SAMPLE_IDX = 0


def get_lidar_points_in_ego(nusc, sample):
    """获取自车坐标系下的激光雷达点云"""
    lidar_token = sample["data"]["LIDAR_TOP"]
    lidar_path = nusc.get_sample_data_path(lidar_token)
    
    sd_record = nusc.get("sample_data", lidar_token)
    cs_record = nusc.get("calibrated_sensor", sd_record["calibrated_sensor_token"])
    pose_record = nusc.get("ego_pose", sd_record["ego_pose_token"])

    # 读取点云
    points = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 5)[:, :3]

    # 激光雷达系 -> 自车系
    rot = Quaternion(cs_record["rotation"]).rotation_matrix
    trans = np.array(cs_record["translation"])
    points_ego = (rot @ points.T).T + trans
    return points_ego


def get_bboxes_in_ego(nusc, sample):
    """获取自车坐标系下的3D标注框：中心xyz、长宽高、航向角yaw"""
    bboxes = []
    for ann_token in sample["anns"]:
        ann = nusc.get("sample_annotation", ann_token)
        # 世界系下的框
        x, y, z = ann["translation"]
        w, l, h = ann["size"]  # nuScenes顺序: 宽、长、高
        yaw = Quaternion(ann["rotation"]).yaw_pitch_roll[0]

        # 转到自车系
        lidar_token = sample["data"]["LIDAR_TOP"]
        sd_record = nusc.get("sample_data", lidar_token)
        pose_record = nusc.get("ego_pose", sd_record["ego_pose_token"])
        ego_rot = Quaternion(pose_record["rotation"]).rotation_matrix
        ego_trans = np.array(pose_record["translation"])

        # 世界->自车
        point_world = np.array([x, y, z])
        point_ego = (ego_rot.T @ (point_world - ego_trans))
        yaw_ego = yaw - Quaternion(pose_record["rotation"]).yaw_pitch_roll[0]

        bboxes.append({
            "x": point_ego[0],
            "y": point_ego[1],
            "l": l,
            "w": w,
            "yaw": yaw_ego,
            "name": ann["category_name"]
        })
    return bboxes


def ego_to_bev_pixel(x, y):
    """自车坐标系(x,y) -> BEV图像像素(u,v)
    约定：自车在BEV图中心，x向前对应图像向上，y向左对应图像向左
    """
    u = int((x - BEV_RANGE[0]) / BEV_RESOLUTION)
    v = int((BEV_RANGE[3] - y) / BEV_RESOLUTION)  # y轴翻转，符合图像坐标系
    return u, v


def draw_bev_bbox(img, bbox, color=(0, 255, 0), thickness=2):
    """在BEV图上绘制带朝向的3D框投影"""
    x, y, l, w, yaw = bbox["x"], bbox["y"], bbox["l"], bbox["w"], bbox["yaw"]

    # 框的四个角点（车辆坐标系下，x向前，y向左）
    corners = np.array([
        [ l/2,  w/2],
        [ l/2, -w/2],
        [-l/2, -w/2],
        [-l/2,  w/2]
    ])

    # 旋转
    rot_mat = np.array([
        [np.cos(yaw), -np.sin(yaw)],
        [np.sin(yaw),  np.cos(yaw)]
    ])
    corners_rot = (rot_mat @ corners.T).T + np.array([x, y])

    # 转BEV像素
    corners_pixel = np.array([ego_to_bev_pixel(cx, cy) for cx, cy in corners_rot], dtype=np.int32)
    cv2.polylines(img, [corners_pixel], True, color, thickness)


def main():
    nusc = NuScenes(version=VERSION, dataroot=NUSCENES_ROOT, verbose=True)
    sample = nusc.sample[SAMPLE_IDX]

    # 1. 获取自车系下的点云
    points_ego = get_lidar_points_in_ego(nusc, sample)
    print(f"自车系点云数量: {len(points_ego)}")

    # 2. 过滤BEV范围内的点
    mask = (points_ego[:, 0] >= BEV_RANGE[0]) & (points_ego[:, 0] <= BEV_RANGE[2]) & \
           (points_ego[:, 1] >= BEV_RANGE[1]) & (points_ego[:, 1] <= BEV_RANGE[3])
    points_bev = points_ego[mask]
    print(f"BEV范围内点云数量: {len(points_bev)}")

    # 3. 创建BEV底图（黑色背景）
    bev_img = np.zeros((BEV_H, BEV_W, 3), dtype=np.uint8)

    # 4. 绘制点云（按高度着色，越高越亮）
    for x, y, z in points_bev:
        u, v = ego_to_bev_pixel(x, y)
        # 高度映射到颜色，z范围-5~3米
        z_norm = np.clip((z + 5) / 8 * 255, 0, 255).astype(np.uint8)
        bev_img[v, u] = [z_norm, 200, 255 - z_norm]  # BGR

    # 5. 绘制标注框（绿色）
    bboxes = get_bboxes_in_ego(nusc, sample)
    for box in bboxes:
        draw_bev_bbox(bev_img, box, color=(0, 255, 0), thickness=2)

    # 6. 标记自车位置（中心红色十字）
    center_u, center_v = ego_to_bev_pixel(0, 0)
    cv2.drawMarker(bev_img, (center_u, center_v), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
    cv2.putText(bev_img, "Ego", (center_u + 5, center_v - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

    cv2.imwrite("bev_result.jpg", bev_img)
    print(f"\n✅ BEV可视化结果已保存为 bev_result.jpg")
    print(f"   BEV尺寸: {BEV_W} x {BEV_H} 像素，对应 100m x 100m 范围")
    print(f"   标注框数量: {len(bboxes)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
