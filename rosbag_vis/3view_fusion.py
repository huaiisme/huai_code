"""三视角融合：BEV + 3D + 右侧三相机面板，逐帧渲染并合成视频。

运行方式：进入本目录后执行 python 3view_fusion.py
"""
import os

import cv2
import imageio
import numpy as np
from tqdm import tqdm

from utils.geometry import (box_ego_to_world, box_world_to_ego_view,
                            world_to_ego_view_3d)
from utils.image import resize_to_height
from utils.tf import (create_tf_matrix, get_yaw_from_matrix, gt_quat_to_yaw,
                      transform_points)
from tools.bag_reader.base import (build_gt_match_map, find_nearest_by_time,
                                   find_nearest_frame, load_gt_json_dir,
                                   load_odom_list_cached, load_pred_csv)
from tools.bag_reader.camera import load_camera_frames_cached
from tools.bag_reader.lidar import load_lidar_frames_cached
from tools.vis.bev import render_bev
from tools.vis.camera_panel import build_camera_panel
from tools.vis.lidar_3d import render_3d

# ===================== 配置 =====================
BAG_PATH = "/home/huai/huai_work/data/eval_260609before/record_2026-06-04-10-20-43.bag"
ODOM_TOPIC = "/gps/odom"
GT_LABEL_SIMPLE_PATH = "/home/huai/huai_work/data/gt_label_simple/record_2026-06-04-10-20-43"
PRED_CSV_PATH = "/home/huai/huai_work/data/pred_simple/record_2026-06-04-10-20-43.csv"

CAMERA_TOPICS = {
    "front":       "/front_camera/cam000",
    "front_left":  "/left_front_camera/cam004",
    "front_right": "/right_front_camera/cam006",
}

LIDAR_CFG_LIST = [
    {"topic": "/front_main_lidar_raw_data",        "tf_xyz": [8.072, 0.053, 1.708], "tf_rpy": [0.002, 0.036, -0.018]},
    {"topic": "/front_left_auxi_lidar_raw_data",   "tf_xyz": [8.154, 2.111, 0.943], "tf_rpy": [0.003, 0.031,  0.802]},
    {"topic": "/front_right_auxi_lidar_raw_data", "tf_xyz": [8.183, -2.002, 0.890], "tf_rpy": [-0.016, 0.027, -0.767]},
    {"topic": "/rear_lidar_raw_data",              "tf_xyz": [-1.744, -0.006, 0.672], "tf_rpy": [-0.003, -0.005, 3.128]},
]

# 可视化
POINT_COLOR = "#48D1CC"
VIEW_RANGE_BEV = 100.0
VIEW_RANGE_X_FRONT = 50.0
VIEW_RANGE_X_BACK = 20.0
VIEW_RANGE_Y = 30.0
VIEW_RANGE_Z_MIN = -2.0
VIEW_RANGE_Z_MAX = 8.0
BOX_CENTER_MARGIN = (5.0, 5.0, 2.0)
AXIS_ASPECT = (1, 1.5, 0.8)
ELEV_ANGLE = 60.0
AZIM_ANGLE = 180.0

# 时间匹配阈值 (ms)
GT_MAX_DIFF_MS = 150
PRED_MAX_DIFF_MS = 150
FRAME_MATCH_THRESHOLD_MS = 50
CAMERA_MAX_DIFF_MS = 100

# 输出
TOTAL_HEIGHT = 900
CAM_RIGHT_WIDTH = 540
CAM_GAP = 0
OUTPUT_DIR = "./3view_fusion_frames"
VIDEO_PATH = "./3view_fusion.mp4"
FPS = 10


# ===================== 框坐标变换 =====================
def transform_gt_to_view(gt_data, odom_T, car_x, car_y, car_z, car_yaw):
    """GT 框：自车系 → 世界系 → 自车视角（与点云同一条变换链）。"""
    out = []
    for obj in gt_data["objects"]:
        ego_yaw = gt_quat_to_yaw(obj["rotation"])
        tx, ty, tz = obj["translation"]
        wx, wy, wz, wyaw = box_ego_to_world(tx, ty, tz, ego_yaw, odom_T)
        vx, vy, vz, vyaw = box_world_to_ego_view(wx, wy, wz, wyaw,
                                                 car_x, car_y, car_z, car_yaw)
        out.append({"ID": obj["ID"], "category": obj["category"],
                    "translation": [vx, vy, vz], "size": obj["size"], "yaw": vyaw})
    return {"objects": out}


def transform_pred_to_view(pred_data, car_x, car_y, car_z, car_yaw):
    """Pred 框：世界系 → 自车视角。"""
    out = []
    for obj in pred_data["objects"]:
        tx, ty, tz = obj["translation"]
        vx, vy, vz, vyaw = box_world_to_ego_view(tx, ty, tz, obj["yaw"],
                                                 car_x, car_y, car_z, car_yaw)
        out.append({"track_id": obj["track_id"], "category": obj["category"],
                    "translation": [vx, vy, vz], "size": obj["size"],
                    "yaw": vyaw, "conf": obj["conf"]})
    return {"objects": out}


def _collect_points(lidar_data, cfg_list, t_ms, odom_T, car_x, car_y, car_z, car_yaw):
    """雷达 → 自车 → 世界 → 自车视角，按时间戳融合多路点云。"""
    pts_rel_list = []
    for cfg in cfg_list:
        frame, dt_ms = find_nearest_frame(lidar_data[cfg["topic"]], t_ms)
        if frame is None or dt_ms > FRAME_MATCH_THRESHOLD_MS:
            continue
        pts_base = transform_points(frame["pts"], cfg["T_lidar"])
        pts_world = transform_points(pts_base, odom_T)
        pts_rel_list.append(world_to_ego_view_3d(pts_world, car_x, car_y, car_z, car_yaw))
    return pts_rel_list


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith(".png"):
            os.remove(os.path.join(OUTPUT_DIR, f))

    print("==== Step1: Loading odom ====")
    odom_list = load_odom_list_cached(BAG_PATH, ODOM_TOPIC)
    print(f"✅ {len(odom_list)} odom")

    print("==== Step2: Loading lidar ====")
    lidar_data = {}
    for cfg in tqdm(LIDAR_CFG_LIST, desc="读取雷达"):
        cfg["T_lidar"] = create_tf_matrix(cfg["tf_xyz"], cfg["tf_rpy"])
        lidar_data[cfg["topic"]] = load_lidar_frames_cached(BAG_PATH, cfg["topic"])

    print("==== Step3: Loading GT & Pred ====")
    gt_list = load_gt_json_dir(GT_LABEL_SIMPLE_PATH)
    pred_list = load_pred_csv(PRED_CSV_PATH)
    print(f"✅ GT: {len(gt_list)}, Pred: {len(pred_list)}")

    print("==== Step4: Loading cameras ====")
    cam_data = {name: load_camera_frames_cached(BAG_PATH, topic)
                for name, topic in CAMERA_TOPICS.items()}

    main_frames = lidar_data[LIDAR_CFG_LIST[0]["topic"]]
    gt_match_map = build_gt_match_map(main_frames, gt_list, GT_MAX_DIFF_MS)
    print(f"✅ GT 匹配成功 {sum(g is not None for g in gt_match_map)} 帧")

    print("==== Step5: Rendering fusion ====")
    image_paths = []
    for idx in tqdm(range(len(main_frames)), desc="渲染"):
        t_ms = main_frames[idx]["t_ms"]
        odom = find_nearest_by_time(odom_list, t_ms)
        car_x, car_y, car_z = odom["T"][0, 3], odom["T"][1, 3], odom["T"][2, 3]
        car_yaw = get_yaw_from_matrix(odom["T"])

        gt_item = gt_match_map[idx]
        pred_item = find_nearest_by_time(pred_list, t_ms) if pred_list else None
        if pred_item and abs(pred_item["t_ms"] - t_ms) > PRED_MAX_DIFF_MS:
            pred_item = None

        pts_rel_list = _collect_points(lidar_data, LIDAR_CFG_LIST, t_ms,
                                       odom["T"], car_x, car_y, car_z, car_yaw)
        gt_view = transform_gt_to_view(gt_item["data"], odom["T"],
                                      car_x, car_y, car_z, car_yaw) if gt_item else None
        pred_view = transform_pred_to_view(pred_item, car_x, car_y, car_z, car_yaw) if pred_item else None

        bev_img, _ = render_bev(pts_rel_list, gt_data=gt_view, pred_data=pred_view,
                                view_range=VIEW_RANGE_BEV, point_color=POINT_COLOR,
                                frame_idx=idx, t_ms=t_ms)
        d3_img, _ = render_3d(pts_rel_list, gt_data=gt_view, pred_data=pred_view,
                              view_x_back=VIEW_RANGE_X_BACK, view_x_front=VIEW_RANGE_X_FRONT,
                              view_y=VIEW_RANGE_Y, view_z_min=VIEW_RANGE_Z_MIN,
                              view_z_max=VIEW_RANGE_Z_MAX, point_color=POINT_COLOR,
                              box_center_margin=BOX_CENTER_MARGIN, axis_aspect=AXIS_ASPECT,
                              elev=ELEV_ANGLE, azim=AZIM_ANGLE, frame_idx=idx, t_ms=t_ms)
        cam_panel = build_camera_panel(cam_data, t_ms, CAMERA_MAX_DIFF_MS,
                                       CAM_RIGHT_WIDTH, CAM_GAP)

        fusion = np.hstack([
            resize_to_height(bev_img, TOTAL_HEIGHT),
            resize_to_height(d3_img, TOTAL_HEIGHT),
            resize_to_height(cam_panel, TOTAL_HEIGHT),
        ])
        img_path = os.path.join(OUTPUT_DIR, f"frame_{idx:04d}.png")
        cv2.imwrite(img_path, fusion)
        image_paths.append(img_path)

    print("==== Step6: Writing video ====")
    writer = imageio.get_writer(VIDEO_PATH, fps=FPS)
    for img_path in tqdm(image_paths, desc="合成视频"):
        writer.append_data(imageio.imread(img_path))
    writer.close()
    print(f"🎉 完成: {VIDEO_PATH}")


if __name__ == "__main__":
    main()
