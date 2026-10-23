import os
import numpy as np
import imageio
from tqdm import tqdm

from utils.tf_utils import create_tf_matrix, transform_points, gt_quat_to_yaw
from utils.bag_utils import (
    load_lidar_frames_cached, find_nearest_frame,
    load_gt_json_dir
)
from utils.vis_utils import corner2boxes_3d, draw_3d_box

# ===================== 配置区 =====================
BAG_PATH = "/mnt/g/Gdisk_data1/eval_260609before/record_2026-06-04-10-19-07.bag"
GT_LABEL_SIMPLE_PATH = "/home/huai/huai_work/data/gt_label_simple/record_2026-06-04-10-19-07"

LIDAR_CFG_LIST = [
    {"topic": "/front_main_lidar_raw_data", "tf_xyz": [8.072, 0.053, 1.708], "tf_rpy": [0.002, 0.036, -0.018]},
    {"topic": "/front_left_auxi_lidar_raw_data", "tf_xyz": [8.154, 2.111, 0.943], "tf_rpy": [0.003, 0.031, 0.802]},
    {"topic": "/front_right_auxi_lidar_raw_data", "tf_xyz": [8.183, -2.002, 0.890], "tf_rpy": [-0.016, 0.027, -0.767]},
    {"topic": "/rear_lidar_raw_data", "tf_xyz": [-1.744, -0.006, 0.672], "tf_rpy": [-0.003, -0.005, 3.128]},
]

POINT_COLOR = '#48D1CC'
GT_COLOR = '#ff3333'

VIEW_RANGE_X = 50.0
VIEW_RANGE_X_BACK = 20.0
VIEW_RANGE_Y = 30.0
VIEW_RANGE_Z_MIN = -2.0
VIEW_RANGE_Z_MAX = 8.0

# GT框中心点过滤冗余（米），中心点在此范围内就显示整框
GT_CENTER_MARGIN_X = 5.0
GT_CENTER_MARGIN_Y = 5.0
GT_CENTER_MARGIN_Z = 2.0

GT_MAX_DIFF_MS = 150      # GT最大允许时间差，超过150ms直接舍弃
FRAME_MATCH_THRESHOLD_MS = 50

AXIS_ASPECT = [1, 1.5, 0.8]
ELEV = 60.0
AZIM = 180.0

OUTPUT_DIR = "./3d_ego_gt_frames"
VIDEO_PATH = "./3d_ego_gt.mp4"
FPS = 10
# =================================================


def process_gt_ego(gt_data):
    """自车版GT：直接用ego坐标，只转yaw"""
    gt_view = {"objects": []}
    for obj in gt_data["objects"]:
        gt_view["objects"].append({
            "ID": obj["ID"],
            "category": obj["category"],
            "translation": obj["translation"],
            "size": obj["size"],
            "yaw": gt_quat_to_yaw(obj["rotation"])
        })
    return gt_view


def build_gt_match_map(radar_frames, gt_list, max_diff_ms):
    """
    全局一对一GT匹配：每个GT只分配给时间最接近的那一帧雷达
    超过 max_diff_ms 的直接舍弃，不参与匹配
    返回：长度等于雷达帧数的数组，每个元素是匹配到的GT项或None
    """
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

    # Step1: 读取雷达（带缓存）
    print("==== Step1: Loading lidar (with cache) ====")
    lidar_data = {}
    for cfg in tqdm(LIDAR_CFG_LIST, desc="读取雷达"):
        cfg["T_lidar"] = create_tf_matrix(cfg["tf_xyz"], cfg["tf_rpy"])
        lidar_data[cfg["topic"]] = load_lidar_frames_cached(BAG_PATH, cfg["topic"])

    # Step2: 读取GT
    print("==== Step2: Loading GT ====")
    gt_list = load_gt_json_dir(GT_LABEL_SIMPLE_PATH)
    print(f"✅ {len(gt_list)} GT frames")

    # Step2.5: 预计算全局一对一GT匹配表
    main_frames = lidar_data[LIDAR_CFG_LIST[0]["topic"]]
    gt_match_map = build_gt_match_map(main_frames, gt_list, GT_MAX_DIFF_MS)
    match_count = sum(1 for g in gt_match_map if g is not None)
    print(f"✅ 匹配成功 {match_count} 帧GT（一对一，超限舍弃）")

    # Step3: 逐帧渲染
    print("==== Step3: Rendering 3D + GT ====")
    image_paths = []

    pbar = tqdm(range(len(main_frames)), desc="渲染")
    for idx in pbar:
        t_ms = main_frames[idx]["t_ms"]
        gt_item = gt_match_map[idx]

        # 按时间戳匹配每路雷达帧并合并
        all_pts_list = []
        for cfg in LIDAR_CFG_LIST:
            frame, dt_ms = find_nearest_frame(lidar_data[cfg["topic"]], t_ms)
            if frame is None or dt_ms > FRAME_MATCH_THRESHOLD_MS:
                continue
            pts_base = transform_points(frame["pts"], cfg["T_lidar"])
            all_pts_list.append(pts_base)

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

        # GT处理
        gt_data_view = process_gt_ego(gt_item["data"]) if gt_item else None

        # 绘图
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        plt.style.use('dark_background')

        fig = plt.figure(figsize=(16, 10), dpi=150)
        ax = fig.add_subplot(111, projection='3d')

        # 画点云
        ax.scatter(
            all_pts[:, 0], all_pts[:, 1], all_pts[:, 2],
            s=0.1, c=POINT_COLOR, alpha=1.0
        )

        # 画GT 3D包围盒（中心点+冗余软过滤，纯线框低透明度）
        if gt_data_view is not None and "objects" in gt_data_view:
            for obj in gt_data_view["objects"]:
                x, y, z = obj["translation"]
                w, l, h = obj["size"]

                # 只按中心点判断，带冗余；边缘超出范围也保留整框
                if (x < -VIEW_RANGE_X_BACK - GT_CENTER_MARGIN_X) or (x > VIEW_RANGE_X + GT_CENTER_MARGIN_X):
                    continue
                if (y < -VIEW_RANGE_Y - GT_CENTER_MARGIN_Y) or (y > VIEW_RANGE_Y + GT_CENTER_MARGIN_Y):
                    continue
                if (z < VIEW_RANGE_Z_MIN - GT_CENTER_MARGIN_Z) or (z > VIEW_RANGE_Z_MAX + GT_CENTER_MARGIN_Z):
                    continue

                corners_3d = corner2boxes_3d(x, y, z, l, w, h, obj["yaw"])
                draw_3d_box(ax, corners_3d, color=GT_COLOR, linestyle='-', linewidth=1.0, alpha=0.35)

        # 坐标轴范围
        ax.set_xlim(-VIEW_RANGE_X_BACK, VIEW_RANGE_X)
        ax.set_ylim(-VIEW_RANGE_Y, VIEW_RANGE_Y)
        ax.set_zlim(VIEW_RANGE_Z_MIN, VIEW_RANGE_Z_MAX)

        # 纯视觉轴比例
        ax.set_box_aspect(AXIS_ASPECT)

        # 标签与标题
        ax.set_xlabel('X (forward, m)', fontsize=12)
        ax.set_ylabel('Y (left, m)', fontsize=12)
        ax.set_zlabel('Z (up, m)', fontsize=12)
        ax.set_title(f'3D EGO + GT - FRAME {idx:04d}  t={t_ms}ms', fontsize=14)

        # 视角
        ax.view_init(elev=ELEV, azim=AZIM)

        # 视觉优化
        ax.grid(False)
        ax.xaxis.pane.set_visible(False)
        ax.yaxis.pane.set_visible(False)
        ax.zaxis.pane.set_visible(False)

        # 保存
        img_path = os.path.join(OUTPUT_DIR, f"frame_{idx:04d}.png")
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close()
        image_paths.append(img_path)
        pbar.set_postfix(pts=all_pts.shape[0], gt="Y" if gt_item else "N")

    # Step4: 合成视频
    print("==== Step4: Writing video ====")
    writer = imageio.get_writer(VIDEO_PATH, fps=FPS)
    for img_path in tqdm(image_paths, desc="合成视频"):
        writer.append_data(imageio.imread(img_path))
    writer.close()
    print(f"🎉 完成: {VIDEO_PATH}")


if __name__ == "__main__":
    main()
