import os
import imageio
from tqdm import tqdm

from utils.tf_utils import create_tf_matrix, transform_points, gt_quat_to_yaw
from utils.bag_utils import load_lidar_frames, load_gt_json_dir, find_nearest_by_time
from utils.vis_utils import draw_bev_frame

# ===================== 配置区 =====================
BAG_PATH = "/mnt/g/Gdisk_data1/eval_0609before/record_2026-06-04-10-19-07.bag"
GT_LABEL_SIMPLE_PATH = "/home/huai/huai_work/data/gt_label_simple/record_2026-06-04-10-19-07"

LIDAR_CFG_LIST = [
    {"topic": "/front_main_lidar_raw_data", "tf_xyz": [8.072, 0.053, 1.708], "tf_rpy": [0.002, 0.036, -0.018]},
    {"topic": "/front_left_auxi_lidar_raw_data", "tf_xyz": [8.154, 2.111, 0.943], "tf_rpy": [0.003, 0.031, 0.802]},
    {"topic": "/front_right_auxi_lidar_raw_data", "tf_xyz": [8.183, -2.002, 0.890], "tf_rpy": [-0.016, 0.027, -0.767]},
    {"topic": "/rear_lidar_raw_data", "tf_xyz": [-1.744, -0.006, 0.672], "tf_rpy": [-0.003, -0.005, 3.128]},
]

VIEW_RANGE = 100.0
POINT_COLOR = '#4A0072'
GT_HOLD_TIME_MS = 100
OUTPUT_DIR = "./ego_frames"
VIDEO_PATH = "./ego_lidar_bev.mp4"
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


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step1: 读取雷达
    print("==== Step1: Loading lidar ====")
    lidar_data = {}
    for cfg in tqdm(LIDAR_CFG_LIST, desc="读取雷达"):
        cfg["T_lidar"] = create_tf_matrix(cfg["tf_xyz"], cfg["tf_rpy"])
        lidar_data[cfg["topic"]] = load_lidar_frames(BAG_PATH, cfg["topic"])

    # Step2: 读取GT
    print("==== Step2: Loading GT ====")
    gt_list = load_gt_json_dir(GT_LABEL_SIMPLE_PATH)
    print(f"✅ {len(gt_list)} GT frames")

    # Step3: 逐帧渲染
    print("==== Step3: Rendering ====")
    image_paths = []
    main_frames = lidar_data[LIDAR_CFG_LIST[0]["topic"]]

    pbar = tqdm(range(len(main_frames)), desc="渲染")
    for idx in pbar:
        t_ms = main_frames[idx]["t_ms"]

        # 匹配GT
        gt_item = None
        if len(gt_list) > 0:
            nearest_gt = find_nearest_by_time(gt_list, t_ms)
            if abs(nearest_gt["t_ms"] - t_ms) <= GT_HOLD_TIME_MS:
                gt_item = nearest_gt

        # 点云变换：雷达 → base_link
        pts_rel_list = []
        for cfg in LIDAR_CFG_LIST:
            if idx >= len(lidar_data[cfg["topic"]]):
                continue
            pts_base = transform_points(lidar_data[cfg["topic"]][idx]["pts"], cfg["T_lidar"])
            pts_rel_list.append(pts_base)

        # GT处理（自车版不需要world变换）
        gt_data_view = process_gt_ego(gt_item["data"]) if gt_item else None

        # 画图
        img_path = os.path.join(OUTPUT_DIR, f"frame_{idx:04d}.png")
        total_pts = draw_bev_frame(
            pts_rel_list=pts_rel_list,
            car_x=0, car_y=0, yaw=0,
            view_range=VIEW_RANGE, point_color=POINT_COLOR,
            frame_idx=idx, t_ms=t_ms,
            gt_data=gt_data_view,
            save_path=img_path
        )
        image_paths.append(img_path)
        pbar.set_postfix(pts=total_pts, gt="Y" if gt_item else "N")

    # Step4: 合成视频
    print("==== Step4: Writing video ====")
    writer = imageio.get_writer(VIDEO_PATH, fps=FPS)
    for img_path in tqdm(image_paths, desc="合成视频"):
        writer.append_data(imageio.imread(img_path))
    writer.close()

    print(f"🎉 完成: {VIDEO_PATH}")


if __name__ == "__main__":
    main()
