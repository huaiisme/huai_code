import os
import imageio
from tqdm import tqdm

from utils.tf_utils import create_tf_matrix, transform_points
from utils.bag_utils import load_lidar_frames

# ===================== 配置区 =====================
BAG_PATH = "/mnt/g/Gdisk_data1/eval_260609before/record_2026-06-04-10-19-07.bag"

LIDAR_CFG_LIST = [
    {"topic": "/front_main_lidar_raw_data", "tf_xyz": [8.072, 0.053, 1.708], "tf_rpy": [0.002, 0.036, -0.018]},
    {"topic": "/front_left_auxi_lidar_raw_data", "tf_xyz": [8.154, 2.111, 0.943], "tf_rpy": [0.003, 0.031, 0.802]},
    {"topic": "/front_right_auxi_lidar_raw_data", "tf_xyz": [8.183, -2.002, 0.890], "tf_rpy": [-0.016, 0.027, -0.767]},
    {"topic": "/rear_lidar_raw_data", "tf_xyz": [-1.744, -0.006, 0.672], "tf_rpy": [-0.003, -0.005, 3.128]},
]

POINT_COLOR = '#4A0072'
VIEW_RANGE_X = 30.0    # 前方50米
VIEW_RANGE_Y = 30.0     # 左右各30米
VIEW_RANGE_Z_MIN = -2.0
VIEW_RANGE_Z_MAX = 8.0

# 等轴测视角（RViz同款）
ELEV = 35.264
AZIM = -45.0

OUTPUT_DIR = "./driver_view_frames"
VIDEO_PATH = "./driver_view.mp4"
FPS = 10
# =================================================


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 读取雷达
    print("==== Loading lidar ====")
    lidar_data = {}
    for cfg in tqdm(LIDAR_CFG_LIST, desc="读取雷达"):
        cfg["T_lidar"] = create_tf_matrix(cfg["tf_xyz"], cfg["tf_rpy"])
        lidar_data[cfg["topic"]] = load_lidar_frames(BAG_PATH, cfg["topic"])

    # 逐帧渲染
    print("==== Rendering 3D pointcloud ====")
    image_paths = []
    main_frames = lidar_data[LIDAR_CFG_LIST[0]["topic"]]

    pbar = tqdm(range(len(main_frames)), desc="渲染")
    for idx in pbar:
        t_ms = main_frames[idx]["t_ms"]

        # 合并所有雷达点云（自车坐标系）
        all_pts = []
        for cfg in LIDAR_CFG_LIST:
            if idx >= len(lidar_data[cfg["topic"]]):
                continue
            pts_base = transform_points(lidar_data[cfg["topic"]][idx]["pts"], cfg["T_lidar"])
            all_pts.append(pts_base)

        if len(all_pts) == 0:
            continue
        all_pts = np.vstack(all_pts)

        # 裁剪范围：只看前方
        # mask = ((all_pts[:, 0] >= 0) & (all_pts[:, 0] <= VIEW_RANGE_X) &
        #         (all_pts[:, 1] >= -VIEW_RANGE_Y) & (all_pts[:, 1] <= VIEW_RANGE_Y) &
        #         (all_pts[:, 2] >= VIEW_RANGE_Z_MIN) & (all_pts[:, 2] <= VIEW_RANGE_Z_MAX))
        # all_pts = all_pts[mask]

        # 画图
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D

        # 深色背景（可选，更像RViz）
        plt.style.use('dark_background')
        
        fig = plt.figure(figsize=(12, 9), dpi=100)
        ax = fig.add_subplot(111, projection='3d')

        # ========== 关键：正交投影 + 等比例 ==========
        ax.set_proj_type('ortho')  # 正交投影，和RViz一致

        ax.scatter(all_pts[:, 0], all_pts[:, 1], all_pts[:, 2],
                   s=0.3, c='#ff4444', alpha=0.8)  # 红色点，接近RViz

        # 坐标轴
        ax.set_xlim(0, VIEW_RANGE_X)
        ax.set_ylim(-VIEW_RANGE_Y, VIEW_RANGE_Y)
        ax.set_zlim(VIEW_RANGE_Z_MIN, VIEW_RANGE_Z_MAX)
        ax.set_xlabel('X (forward, m)')
        ax.set_ylabel('Y (left, m)')
        ax.set_zlabel('Z (up, m)')
        ax.set_title(f'3D Pointcloud - FRAME {idx:04d}  t={t_ms}ms')
        
        # 等轴测视角（和RViz默认视角一致）
        ax.view_init(elev=35.264, azim=-45)

        # 去掉多余边框
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False

        img_path = os.path.join(OUTPUT_DIR, f"frame_{idx:04d}.png")
        plt.savefig(img_path, dpi=100, bbox_inches='tight')
        plt.close()
        image_paths.append(img_path)
        pbar.set_postfix(pts=all_pts.shape[0])

    # 合成视频
    print("==== Writing video ====")
    writer = imageio.get_writer(VIDEO_PATH, fps=FPS)
    for img_path in tqdm(image_paths, desc="合成视频"):
        writer.append_data(imageio.imread(img_path))
    writer.close()

    print(f"🎉 完成: {VIDEO_PATH}")


if __name__ == "__main__":
    import numpy as np
    main()
