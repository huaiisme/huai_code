"""3D 视图：世界系坐标下点云 + GT/Pred 3D 框，逐帧渲染并合成视频。

运行方式：进入本目录后执行 python 3d_view_world_with_gt_pred.py
"""
import os

import imageio
from tqdm import tqdm

from utils.geometry import (box_ego_to_world, box_world_to_ego_view,
                            world_to_ego_view_3d)
from utils.tf import (create_tf_matrix, get_yaw_from_matrix, gt_quat_to_yaw,
                      transform_points)
from tools.bag_reader.base import (build_gt_match_map, find_nearest_by_time,
                                   find_nearest_frame, load_gt_json_dir,
                                   load_odom_list_cached, load_pred_csv)
from tools.bag_reader.lidar import load_lidar_frames_cached
from tools.vis.lidar_3d import draw_3d_frame

# ===================== 配置 =====================
BAG_PATH = "/mnt/g/Gdisk_data1/eval_260609before/record_2026-06-04-10-19-07.bag"
ODOM_TOPIC = "/gps/odom"
GT_LABEL_SIMPLE_PATH = "/home/huai/huai_work/data/gt_label_simple/record_2026-06-04-10-19-07"
PRED_PATH = "/home/huai/huai_work/data/pred_simple/record_2026-06-04-10-19-07.csv"

LIDAR_CFG_LIST = [
    {"topic": "/front_main_lidar_raw_data",        "tf_xyz": [8.072, 0.053, 1.708], "tf_rpy": [0.002, 0.036, -0.018]},
    {"topic": "/front_left_auxi_lidar_raw_data",   "tf_xyz": [8.154, 2.111, 0.943], "tf_rpy": [0.003, 0.031,  0.802]},
    {"topic": "/front_right_auxi_lidar_raw_data", "tf_xyz": [8.183, -2.002, 0.890], "tf_rpy": [-0.016, 0.027, -0.767]},
    {"topic": "/rear_lidar_raw_data",              "tf_xyz": [-1.744, -0.006, 0.672], "tf_rpy": [-0.003, -0.005, 3.128]},
]

POINT_COLOR = "#48D1CC"
VIEW_X_FRONT = 50.0
VIEW_X_BACK = 20.0
VIEW_Y = 30.0
VIEW_Z_MIN = -2.0
VIEW_Z_MAX = 8.0
BOX_CENTER_MARGIN = (5.0, 5.0, 2.0)
AXIS_ASPECT = (1, 1.5, 0.8)
ELEV = 60.0
AZIM = 180.0

GT_MAX_DIFF_MS = 150
PRED_MAX_DIFF_MS = 150
FRAME_MATCH_THRESHOLD_MS = 50

OUTPUT_DIR = "./3d_view_world_coord_gt_pred_frames"
VIDEO_PATH = "./3d_view_world_coord_gt_pred.mp4"
FPS = 10


# ===================== 框坐标变换 =====================
def process_gt_global(gt_data, odom_T, car_x, car_y, car_z, car_yaw):
    out = []
    for obj in gt_data["objects"]:
        ego_yaw = gt_quat_to_yaw(obj["rotation"])
        wx, wy, wz, wyaw = box_ego_to_world(obj["translation"][0], obj["translation"][1],
                                            obj["translation"][2], ego_yaw, odom_T)
        vx, vy, vz, vyaw = box_world_to_ego_view(wx, wy, wz, wyaw,
                                                 car_x, car_y, car_z, car_yaw)
        out.append({"ID": obj["ID"], "category": obj["category"],
                    "translation": [vx, vy, vz], "size": obj["size"], "yaw": vyaw})
    return {"objects": out}


def process_pred_world(pred_data, car_x, car_y, car_z, car_yaw):
    out = []
    for obj in pred_data["objects"]:
        vx, vy, vz, vyaw = box_world_to_ego_view(obj["translation"][0], obj["translation"][1],
                                                obj["translation"][2], obj["yaw"],
                                                car_x, car_y, car_z, car_yaw)
        out.append({"track_id": obj["track_id"], "category": obj["category"],
                    "translation": [vx, vy, vz], "size": obj["size"],
                    "yaw": vyaw, "conf": obj["conf"]})
    return {"objects": out}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("==== Step1: Loading odom ====")
    odom_list = load_odom_list_cached(BAG_PATH, ODOM_TOPIC)
    print(f"✅ {len(odom_list)} odom")

    print("==== Step2: Loading lidar ====")
    lidar_data = {}
    for cfg in tqdm(LIDAR_CFG_LIST, desc="读取雷达"):
        cfg["T_lidar"] = create_tf_matrix(cfg["tf_xyz"], cfg["tf_rpy"])
        lidar_data[cfg["topic"]] = load_lidar_frames_cached(BAG_PATH, cfg["topic"])

    print("==== Step3: Loading GT ====")
    gt_list = load_gt_json_dir(GT_LABEL_SIMPLE_PATH)
    print(f"✅ {len(gt_list)} GT frames")

    print("==== Step4: Loading Pred ====")
    pred_list = load_pred_csv(PRED_PATH)
    print(f"✅ {len(pred_list)} Pred frames")

    main_frames = lidar_data[LIDAR_CFG_LIST[0]["topic"]]
    gt_match_map = build_gt_match_map(main_frames, gt_list, GT_MAX_DIFF_MS)
    print(f"✅ GT 匹配成功 {sum(g is not None for g in gt_match_map)} 帧")

    print("==== Step5: Rendering ====")
    image_paths = []
    pbar = tqdm(range(len(main_frames)), desc="渲染")
    for idx in pbar:
        t_ms = main_frames[idx]["t_ms"]
        odom = find_nearest_by_time(odom_list, t_ms)
        car_x, car_y, car_z = odom["T"][0, 3], odom["T"][1, 3], odom["T"][2, 3]
        car_yaw = get_yaw_from_matrix(odom["T"])

        gt_item = gt_match_map[idx]
        pred_item = find_nearest_by_time(pred_list, t_ms) if pred_list else None
        if pred_item and abs(pred_item["t_ms"] - t_ms) > PRED_MAX_DIFF_MS:
            pred_item = None

        pts_rel_list = []
        for cfg in LIDAR_CFG_LIST:
            frame, dt_ms = find_nearest_frame(lidar_data[cfg["topic"]], t_ms)
            if frame is None or dt_ms > FRAME_MATCH_THRESHOLD_MS:
                continue
            pts_base = transform_points(frame["pts"], cfg["T_lidar"])
            pts_world = transform_points(pts_base, odom["T"])
            pts_rel_list.append(world_to_ego_view_3d(pts_world, car_x, car_y, car_z, car_yaw))

        gt_view = process_gt_global(gt_item["data"], odom["T"],
                                    car_x, car_y, car_z, car_yaw) if gt_item else None
        pred_view = process_pred_world(pred_item, car_x, car_y, car_z, car_yaw) if pred_item else None

        img_path = os.path.join(OUTPUT_DIR, f"frame_{idx:04d}.png")
        total_pts = draw_3d_frame(
            pts_rel_list=pts_rel_list,
            view_x_back=VIEW_X_BACK, view_x_front=VIEW_X_FRONT,
            view_y=VIEW_Y, view_z_min=VIEW_Z_MIN, view_z_max=VIEW_Z_MAX,
            point_color=POINT_COLOR, gt_data=gt_view, pred_data=pred_view,
            box_center_margin=BOX_CENTER_MARGIN, axis_aspect=AXIS_ASPECT,
            elev=ELEV, azim=AZIM, frame_idx=idx, t_ms=t_ms, save_path=img_path)
        image_paths.append(img_path)
        pbar.set_postfix(pts=total_pts, gt="Y" if gt_item else "N",
                         pred="Y" if pred_item else "N")

    print("==== Step6: Writing video ====")
    writer = imageio.get_writer(VIDEO_PATH, fps=FPS)
    for img_path in tqdm(image_paths, desc="合成视频"):
        writer.append_data(imageio.imread(img_path))
    writer.close()
    print(f"🎉 完成: {VIDEO_PATH}")


if __name__ == "__main__":
    main()
