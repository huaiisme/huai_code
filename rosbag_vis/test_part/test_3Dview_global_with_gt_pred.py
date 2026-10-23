import os
import numpy as np
import imageio
from tqdm import tqdm

from utils.tf_utils import (
    create_tf_matrix, get_yaw_from_matrix,
    transform_points, gt_quat_to_yaw, gt_ego_to_world, gt_world_to_ego_view
)
from utils.bag_utils import (
    load_lidar_frames_cached, load_odom_list_cached,
    find_nearest_frame, find_nearest_by_time,
    load_gt_json_dir, load_pred_csv
)
from utils.vis_utils import corner2boxes_3d, draw_3d_box

# ===================== 配置区 =====================
BAG_PATH = "/mnt/g/Gdisk_data1/eval_260609before/record_2026-06-04-10-19-07.bag"
ODOM_TOPIC = "/gps/odom"
GT_LABEL_SIMPLE_PATH = "/home/huai/huai_work/data/gt_label_simple/record_2026-06-04-10-19-07"
PRED_PATH = "/home/huai/huai_work/data/pred_simple/record_2026-06-04-10-19-07.csv"

LIDAR_CFG_LIST = [
    {"topic": "/front_main_lidar_raw_data", "tf_xyz": [8.072, 0.053, 1.708], "tf_rpy": [0.002, 0.036, -0.018]},
    {"topic": "/front_left_auxi_lidar_raw_data", "tf_xyz": [8.154, 2.111, 0.943], "tf_rpy": [0.003, 0.031, 0.802]},
    {"topic": "/front_right_auxi_lidar_raw_data", "tf_xyz": [8.183, -2.002, 0.890], "tf_rpy": [-0.016, 0.027, -0.767]},
    {"topic": "/rear_lidar_raw_data", "tf_xyz": [-1.744, -0.006, 0.672], "tf_rpy": [-0.003, -0.005, 3.128]},
]

POINT_COLOR = '#48D1CC'
GT_COLOR = '#ff3333'
PRED_COLOR = '#33ff66'

VIEW_RANGE_X = 50.0
VIEW_RANGE_X_BACK = 20.0
VIEW_RANGE_Y = 30.0
VIEW_RANGE_Z_MIN = -2.0
VIEW_RANGE_Z_MAX = 8.0

BOX_CENTER_MARGIN_X = 5.0
BOX_CENTER_MARGIN_Y = 5.0
BOX_CENTER_MARGIN_Z = 2.0

GT_MAX_DIFF_MS = 150
PRED_MAX_DIFF_MS = 150
FRAME_MATCH_THRESHOLD_MS = 50

AXIS_ASPECT = [1, 1.5, 0.8]
ELEV = 60.0
AZIM = 180.0

OUTPUT_DIR = "./3d_global_gt_pred_frames"
VIDEO_PATH = "./3d_global_gt_pred.mp4"
FPS = 10
# =================================================


def world_to_ego_view_3d(pts_world, car_x, car_y, car_z, car_yaw):
    """3D版本：世界系 → 自车系（XY旋转平移，Z仅平移）"""
    dx = pts_world[:, 0] - car_x
    dy = pts_world[:, 1] - car_y
    cos_yaw = np.cos(-car_yaw)
    sin_yaw = np.sin(-car_yaw)

    x = dx * cos_yaw - dy * sin_yaw
    y = dx * sin_yaw + dy * cos_yaw
    z = pts_world[:, 2] - car_z  # Z轴只做平移，对齐自车原点

    return np.column_stack([x, y, z])

def process_gt_global(gt_data, odom_T, car_x, car_y, car_z, car_yaw):
    """GT：ego → world → ego_view，复用点云同款变换，保证严格对齐"""
    gt_view = {"objects": []}
    for obj in gt_data["objects"]:
        # 1. 自车系下的原始坐标
        ego_x, ego_y, ego_z = obj["translation"]
        ego_yaw = gt_quat_to_yaw(obj["rotation"])

        # 2. 中心点：ego → world（和点云用完全一样的矩阵变换）
        center_ego = np.array([[ego_x, ego_y, ego_z]])
        center_world = transform_points(center_ego, odom_T)

        # 3. 中心点：world → ego_view（和点云用完全一样的变换）
        center_view = world_to_ego_view_3d(center_world, car_x, car_y, car_z, car_yaw)
        view_x, view_y, view_z = center_view[0]

        # 4. 航向角：world_yaw = ego_yaw + car_yaw；view_yaw = world_yaw - car_yaw = ego_yaw
        view_yaw = ego_yaw

        gt_view["objects"].append({
            "ID": obj["ID"],
            "category": obj["category"],
            "translation": [view_x, view_y, view_z],
            "size": obj["size"],
            "yaw": view_yaw
        })
    return gt_view


def process_pred_world(pred_data, car_x, car_y, car_z, car_yaw):
    """Pred：world → ego_view，复用点云同款变换"""
    pred_view = {"objects": []}
    for obj in pred_data["objects"]:
        world_x, world_y, world_z = obj["translation"]

        # 中心点 world → ego_view，和点云逻辑完全一致
        center_world = np.array([[world_x, world_y, world_z]])
        center_view = world_to_ego_view_3d(center_world, car_x, car_y, car_z, car_yaw)
        view_x, view_y, view_z = center_view[0]

        # 航向角减去自车航向
        view_yaw = obj["yaw"] - car_yaw

        pred_view["objects"].append({
            "track_id": obj["track_id"],
            "category": obj["category"],
            "translation": [view_x, view_y, view_z],
            "size": obj["size"],
            "yaw": view_yaw,
            "conf": obj["conf"]
        })
    return pred_view



def build_gt_match_map(radar_frames, gt_list, max_diff_ms):
    radar_times = np.array([f["t_ms"] for f in radar_frames])
    match_map = [None] * len(radar_frames)
    match_dt = [1e18] * len(radar_frames)

    for gt_item in gt_list:
        gt_t = gt_item["t_ms"]
        diffs = np.abs(radar_times - gt_t)
        nearest_radar_idx = int(np.argmin(diffs))
        dt = diffs[nearest_radar_idx]

        if dt > max_diff_ms:
            continue
        if dt < match_dt[nearest_radar_idx]:
            match_map[nearest_radar_idx] = gt_item
            match_dt[nearest_radar_idx] = dt
    return match_map


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step1: 读取odom（带缓存）
    print("==== Step1: Loading odom (with cache) ====")
    odom_list = load_odom_list_cached(BAG_PATH, ODOM_TOPIC)
    print(f"✅ {len(odom_list)} odom")

    # Step2: 读取雷达（带缓存）
    print("==== Step2: Loading lidar (with cache) ====")
    lidar_data = {}
    for cfg in tqdm(LIDAR_CFG_LIST, desc="读取雷达"):
        cfg["T_lidar"] = create_tf_matrix(cfg["tf_xyz"], cfg["tf_rpy"])
        lidar_data[cfg["topic"]] = load_lidar_frames_cached(BAG_PATH, cfg["topic"])

    # Step3: 读取GT
    print("==== Step3: Loading GT ====")
    gt_list = load_gt_json_dir(GT_LABEL_SIMPLE_PATH)
    print(f"✅ {len(gt_list)} GT frames")

    # Step4: 读取Pred
    print("==== Step4: Loading Pred ====")
    pred_list = load_pred_csv(PRED_PATH)
    print(f"✅ {len(pred_list)} Pred frames")

    # Step4.5: GT全局一对一匹配
    main_frames = lidar_data[LIDAR_CFG_LIST[0]["topic"]]
    gt_match_map = build_gt_match_map(main_frames, gt_list, GT_MAX_DIFF_MS)
    match_count = sum(1 for g in gt_match_map if g is not None)
    print(f"✅ GT匹配成功 {match_count} 帧（一对一，超限舍弃）")

    # Step5: 逐帧渲染
    print("==== Step5: Rendering 3D + GT + Pred ====")
    image_paths = []
    pbar = tqdm(range(len(main_frames)), desc="渲染")

    for idx in pbar:
        t_ms = main_frames[idx]["t_ms"]

        # 匹配odom，提取自车位置和航向
        odom = find_nearest_by_time(odom_list, t_ms)
        car_x = odom["T"][0, 3]
        car_y = odom["T"][1, 3]
        car_z = odom["T"][2, 3]   # 新增：自车世界Z高度
        car_yaw = get_yaw_from_matrix(odom["T"])

        # 匹配GT / Pred
        gt_item = gt_match_map[idx]
        pred_item = None
        if len(pred_list) > 0:
            nearest_pred = find_nearest_by_time(pred_list, t_ms)
            if abs(nearest_pred["t_ms"] - t_ms) <= PRED_MAX_DIFF_MS:
                pred_item = nearest_pred

        # 点云变换：雷达 → base_link → world → ego_view（3D完整版）
        all_pts_list = []
        for cfg in LIDAR_CFG_LIST:
            frame, dt_ms = find_nearest_frame(lidar_data[cfg["topic"]], t_ms)
            if frame is None or dt_ms > FRAME_MATCH_THRESHOLD_MS:
                continue
            pts_base = transform_points(frame["pts"], cfg["T_lidar"])
            pts_world = transform_points(pts_base, odom["T"])
            pts_rel = world_to_ego_view_3d(pts_world, car_x, car_y, car_z, car_yaw)
            all_pts_list.append(pts_rel)

        if len(all_pts_list) == 0:
            continue
        all_pts = np.vstack(all_pts_list)

        # 点云硬裁剪
        mask = (
            (all_pts[:, 0] >= -VIEW_RANGE_X_BACK) & (all_pts[:, 0] <= VIEW_RANGE_X) &
            (all_pts[:, 1] >= -VIEW_RANGE_Y) & (all_pts[:, 1] <= VIEW_RANGE_Y) &
            (all_pts[:, 2] >= VIEW_RANGE_Z_MIN) & (all_pts[:, 2] <= VIEW_RANGE_Z_MAX)
        )
        all_pts = all_pts[mask]

        # GT/Pred 坐标变换
        gt_data_view = process_gt_global(gt_item["data"], odom["T"], car_x, car_y, car_z, car_yaw) if gt_item else None
        pred_data_view = process_pred_world(pred_item, car_x, car_y, car_z, car_yaw) if pred_item else None

        # 绘图
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        plt.style.use('dark_background')

        fig = plt.figure(figsize=(16, 10), dpi=150)
        ax = fig.add_subplot(111, projection='3d')

        ax.scatter(
            all_pts[:, 0], all_pts[:, 1], all_pts[:, 2],
            s=0.1, c=POINT_COLOR, alpha=1.0
        )

        # GT 3D框
        if gt_data_view is not None and "objects" in gt_data_view:
            for obj in gt_data_view["objects"]:
                x, y, z = obj["translation"]
                w, l, h = obj["size"]
                if (x < -VIEW_RANGE_X_BACK - BOX_CENTER_MARGIN_X) or (x > VIEW_RANGE_X + BOX_CENTER_MARGIN_X):
                    continue
                if (y < -VIEW_RANGE_Y - BOX_CENTER_MARGIN_Y) or (y > VIEW_RANGE_Y + BOX_CENTER_MARGIN_Y):
                    continue
                if (z < VIEW_RANGE_Z_MIN - BOX_CENTER_MARGIN_Z) or (z > VIEW_RANGE_Z_MAX + BOX_CENTER_MARGIN_Z):
                    continue
                corners_3d = corner2boxes_3d(x, y, z, l, w, h, obj["yaw"])
                draw_3d_box(ax, corners_3d, color=GT_COLOR, linestyle='-', linewidth=1.0, alpha=0.8)

        # Pred 3D框
        if pred_data_view is not None and "objects" in pred_data_view:
            for obj in pred_data_view["objects"]:
                x, y, z = obj["translation"]
                w, l, h = obj["size"]
                if (x < -VIEW_RANGE_X_BACK - BOX_CENTER_MARGIN_X) or (x > VIEW_RANGE_X + BOX_CENTER_MARGIN_X):
                    continue
                if (y < -VIEW_RANGE_Y - BOX_CENTER_MARGIN_Y) or (y > VIEW_RANGE_Y + BOX_CENTER_MARGIN_Y):
                    continue
                if (z < VIEW_RANGE_Z_MIN - BOX_CENTER_MARGIN_Z) or (z > VIEW_RANGE_Z_MAX + BOX_CENTER_MARGIN_Z):
                    continue
                corners_3d = corner2boxes_3d(x, y, z, l, w, h, obj["yaw"])
                draw_3d_box(ax, corners_3d, color=PRED_COLOR, linestyle='--', linewidth=1.0, alpha=0.8)

        ax.set_xlim(-VIEW_RANGE_X_BACK, VIEW_RANGE_X)
        ax.set_ylim(-VIEW_RANGE_Y, VIEW_RANGE_Y)
        ax.set_zlim(VIEW_RANGE_Z_MIN, VIEW_RANGE_Z_MAX)
        ax.set_box_aspect(AXIS_ASPECT)

        ax.set_xlabel('X (forward, m)', fontsize=12)
        ax.set_ylabel('Y (left, m)', fontsize=12)
        ax.set_zlabel('Z (up, m)', fontsize=12)
        ax.set_title(f'3D Global + GT + Pred - FRAME {idx:04d}  t={t_ms}ms', fontsize=14)

        ax.view_init(elev=ELEV, azim=AZIM)
        ax.grid(False)
        ax.xaxis.pane.set_visible(False)
        ax.yaxis.pane.set_visible(False)
        ax.zaxis.pane.set_visible(False)

        img_path = os.path.join(OUTPUT_DIR, f"frame_{idx:04d}.png")
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close()
        image_paths.append(img_path)

        pbar.set_postfix(
            pts=all_pts.shape[0],
            gt="Y" if gt_item else "N",
            pred="Y" if pred_item else "N"
        )

    # Step6: 合成视频
    print("==== Step6: Writing video ====")
    writer = imageio.get_writer(VIDEO_PATH, fps=FPS)
    for img_path in tqdm(image_paths, desc="合成视频"):
        writer.append_data(imageio.imread(img_path))
    writer.close()
    print(f"🎉 完成: {VIDEO_PATH}")


if __name__ == "__main__":
    main()
