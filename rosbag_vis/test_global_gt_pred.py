import os
import imageio
from tqdm import tqdm

from utils.tf_utils import (
    create_tf_matrix, get_yaw_from_matrix,
    transform_points, world_to_ego_view,
    gt_quat_to_yaw, gt_ego_to_world, gt_world_to_ego_view
)
from utils.bag_utils import (
    load_odom_list, load_lidar_frames,
    load_gt_json_dir, load_pred_csv, find_nearest_by_time
)
from utils.vis_utils import draw_bev_frame

# ===================== 配置区 =====================
BAG_PATH = "/home/huai/huai_work/data/eval_260609before/record_2026-06-04-10-20-43.bag"
ODOM_TOPIC = "/gps/odom"
GT_LABEL_SIMPLE_PATH = "/home/huai/huai_work/data/gt_label_simple/record_2026-06-04-10-20-43"
PRED_CSV_PATH = "/home/huai/huai_work/data/pred_simple/record_2026-06-04-10-20-43.csv"

LIDAR_CFG_LIST = [
    {"topic": "/front_main_lidar_raw_data", "tf_xyz": [8.072, 0.053, 1.708], "tf_rpy": [0.002, 0.036, -0.018]},
    {"topic": "/front_left_auxi_lidar_raw_data", "tf_xyz": [8.154, 2.111, 0.943], "tf_rpy": [0.003, 0.031, 0.802]},
    {"topic": "/front_right_auxi_lidar_raw_data", "tf_xyz": [8.183, -2.002, 0.890], "tf_rpy": [-0.016, 0.027, -0.767]},
    {"topic": "/rear_lidar_raw_data", "tf_xyz": [-1.744, -0.006, 0.672], "tf_rpy": [-0.003, -0.005, 3.128]},
]

VIEW_RANGE = 100.0
POINT_COLOR = '#4A0072'
GT_HOLD_TIME_MS = 100
PRED_HOLD_TIME_MS = 100
OUTPUT_DIR = "./global_gt_pred_frames"
VIDEO_PATH = "./global_gt_pred_bev.mp4"
FPS = 10
# =================================================


def process_gt_global(gt_data, odom_T, car_x, car_y, car_yaw):
    """GT：ego → world → ego_view"""
    gt_view = {"objects": []}
    for obj in gt_data["objects"]:
        obj_yaw_ego = gt_quat_to_yaw(obj["rotation"])
        world_x, world_y, world_yaw = gt_ego_to_world(obj["translation"], obj_yaw_ego, odom_T)
        view_x, view_y, view_yaw = gt_world_to_ego_view(world_x, world_y, world_yaw, car_x, car_y, car_yaw)
        gt_view["objects"].append({
            "ID": obj["ID"],
            "category": obj["category"],
            "translation": [view_x, view_y, obj["translation"][2]],
            "size": obj["size"],
            "yaw": view_yaw
        })
    return gt_view


def process_pred_global(pred_data, car_x, car_y, car_yaw):
    """Pred：已经是world坐标 → 直接转ego_view"""
    pred_view = {"objects": []}
    for obj in pred_data["objects"]:
        view_x, view_y, view_yaw = gt_world_to_ego_view(
            obj["translation"][0], obj["translation"][1], obj["yaw"],
            car_x, car_y, car_yaw
        )
        pred_view["objects"].append({
            "track_id": obj["track_id"],
            "category": obj["category"],
            "translation": [view_x, view_y, obj["translation"][2]],
            "size": obj["size"],
            "yaw": view_yaw,
            "conf": obj["conf"]
        })
    return pred_view


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step1: 读取odom
    print("==== Step1: Loading odom ====")
    odom_list = load_odom_list(BAG_PATH, ODOM_TOPIC)
    print(f"✅ {len(odom_list)} odom")

    # Step2: 读取雷达
    print("==== Step2: Loading lidar ====")
    lidar_data = {}
    for cfg in tqdm(LIDAR_CFG_LIST, desc="读取雷达"):
        cfg["T_lidar"] = create_tf_matrix(cfg["tf_xyz"], cfg["tf_rpy"])
        lidar_data[cfg["topic"]] = load_lidar_frames(BAG_PATH, cfg["topic"])

    # Step3: 读取GT和Pred
    print("==== Step3: Loading GT & Pred ====")
    gt_list = load_gt_json_dir(GT_LABEL_SIMPLE_PATH)
    pred_list = load_pred_csv(PRED_CSV_PATH)
    print(f"✅ GT: {len(gt_list)} frames, Pred: {len(pred_list)} frames")

    # Step4: 逐帧渲染
    print("==== Step4: Rendering ====")
    image_paths = []
    main_frames = lidar_data[LIDAR_CFG_LIST[0]["topic"]]

    pbar = tqdm(range(len(main_frames)), desc="渲染")
    for idx in pbar:
        t_ms = main_frames[idx]["t_ms"]

        odom = find_nearest_by_time(odom_list, t_ms)
        car_x, car_y = odom["T"][0, 3], odom["T"][1, 3]
        car_yaw = get_yaw_from_matrix(odom["T"])

        # 匹配GT
        gt_item = None
        if len(gt_list) > 0:
            nearest_gt = find_nearest_by_time(gt_list, t_ms)
            if abs(nearest_gt["t_ms"] - t_ms) <= GT_HOLD_TIME_MS:
                gt_item = nearest_gt

        # 匹配Pred
        pred_item = None
        if len(pred_list) > 0:
            nearest_pred = find_nearest_by_time(pred_list, t_ms)
            if abs(nearest_pred["t_ms"] - t_ms) <= PRED_HOLD_TIME_MS:
                pred_item = nearest_pred

        # 点云变换
        pts_rel_list = []
        for cfg in LIDAR_CFG_LIST:
            if idx >= len(lidar_data[cfg["topic"]]):
                continue
            pts_base = transform_points(lidar_data[cfg["topic"]][idx]["pts"], cfg["T_lidar"])
            pts_world = transform_points(pts_base, odom["T"])
            pts_rel = world_to_ego_view(pts_world, car_x, car_y, car_yaw)
            pts_rel_list.append(pts_rel)

        # GT和Pred处理
        gt_data_view = process_gt_global(gt_item["data"], odom["T"], car_x, car_y, car_yaw) if gt_item else None
        pred_data_view = process_pred_global(pred_item, car_x, car_y, car_yaw) if pred_item else None

        # 画图
        img_path = os.path.join(OUTPUT_DIR, f"frame_{idx:04d}.png")
        total_pts = draw_bev_frame(
            pts_rel_list=pts_rel_list,
            car_x=car_x, car_y=car_y, yaw=car_yaw,
            view_range=VIEW_RANGE, point_color=POINT_COLOR,
            frame_idx=idx, t_ms=t_ms,
            gt_data=gt_data_view,
            pred_data=pred_data_view,
            save_path=img_path
        )
        image_paths.append(img_path)
        pbar.set_postfix(pts=total_pts, gt="Y" if gt_item else "N", pred="Y" if pred_item else "N")

    # Step5: 合成视频
    print("==== Step5: Writing video ====")
    writer = imageio.get_writer(VIDEO_PATH, fps=FPS)
    for img_path in tqdm(image_paths, desc="合成视频"):
        writer.append_data(imageio.imread(img_path))
    writer.close()

    print(f"🎉 完成: {VIDEO_PATH}")


if __name__ == "__main__":
    main()
