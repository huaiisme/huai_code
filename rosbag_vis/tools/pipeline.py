"""批量 bag 渲染流水线：把三视角融合（BEV + 3D + 相机面板）抽成可复用函数。

入口脚本只负责：
  1. 配置根路径（BAG_ROOTS / GT_ROOT / PRED_ROOT）
  2. discover_bags() 枚举待处理 bag
  3. 循环 run_one_bag()

每个 bag 独立输出到 OUTPUT_ROOT/{bag_name}/，缓存由 bag_reader 自动落在 bag 同级。
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


# ---------------- 框变换（与原 3view_fusion.py 一致） ----------------
def _transform_gt_to_view(gt_data, odom_T, car_x, car_y, car_z, car_yaw):
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


def _transform_pred_to_view(pred_data, car_x, car_y, car_z, car_yaw):
    out = []
    for obj in pred_data["objects"]:
        tx, ty, tz = obj["translation"]
        vx, vy, vz, vyaw = box_world_to_ego_view(tx, ty, tz, obj["yaw"],
                                                 car_x, car_y, car_z, car_yaw)
        out.append({"track_id": obj["track_id"], "category": obj["category"],
                    "translation": [vx, vy, vz], "size": obj["size"],
                    "yaw": vyaw, "conf": obj["conf"]})
    return {"objects": out}


def _collect_points(lidar_data, cfg_list, t_ms, odom_T,
                    car_x, car_y, car_z, car_yaw, frame_match_ms):
    pts_rel_list = []
    for c in cfg_list:
        frame, dt_ms = find_nearest_frame(lidar_data[c["topic"]], t_ms)
        if frame is None or dt_ms > frame_match_ms:
            continue
        pts_base = transform_points(frame["pts"], c["T_lidar"])
        pts_world = transform_points(pts_base, odom_T)
        pts_rel_list.append(world_to_ego_view_3d(pts_world, car_x, car_y, car_z, car_yaw))
    return pts_rel_list


# ---------------- bag 枚举 ----------------
def discover_bags(bag_roots, gt_root, pred_root):
    """扫描 bag_roots 下所有 .bag，自动拼 gt_dir / pred_csv。

    只保留 gt_dir 存在的 bag（调试期 simple 只有 2 个有 GT，其余自动跳过）。
    返回 [{"bag_path", "gt_dir", "pred_csv"}]
    """
    tasks = []
    skipped = 0
    for root in bag_roots:
        if not os.path.isdir(root):
            print(f"⚠️ bag 目录不存在: {root}")
            continue
        for fname in sorted(os.listdir(root)):
            if not fname.endswith(".bag"):
                continue
            bag_path = os.path.join(root, fname)
            bag_name = fname[:-len(".bag")]
            gt_dir = os.path.join(gt_root, bag_name)
            pred_csv = os.path.join(pred_root, f"{bag_name}.csv")
            if not os.path.isdir(gt_dir):
                skipped += 1
                continue
            tasks.append({"bag_path": bag_path, "gt_dir": gt_dir,
                          "pred_csv": pred_csv})
    if skipped:
        print(f"  (其中 {skipped} 个 bag 无对应 GT 目录，已跳过)")
    return tasks


# ---------------- 单 bag 渲染 ----------------
def run_one_bag(bag_path, gt_dir, pred_csv, cfg):
    """跑一个 bag 的三视角融合渲染，输出 mp4 到 OUTPUT_ROOT/{bag_name}/。"""
    bag_name = os.path.basename(bag_path)[:-len(".bag")]
    out_dir = os.path.join(cfg["OUTPUT_ROOT"], bag_name)
    frames_dir = os.path.join(out_dir, "frames")
    video_path = os.path.join(out_dir, f"{bag_name}.mp4")
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        if f.endswith(".png"):
            os.remove(os.path.join(frames_dir, f))

    print(f"\n========== [{bag_name}] ==========")
    print(f"  bag  : {bag_path}")
    print(f"  gt   : {gt_dir}")
    print(f"  pred : {pred_csv}")

    print("  Step1: odom")
    odom_list = load_odom_list_cached(bag_path, cfg["ODOM_TOPIC"])
    if not odom_list:
        print("  ⚠️ odom 为空，跳过")
        return False

    print("  Step2: lidar")
    lidar_data = {}
    for c in tqdm(cfg["LIDAR_CFG_LIST"], desc="    雷达"):
        lidar_data[c["topic"]] = load_lidar_frames_cached(bag_path, c["topic"])

    print("  Step3: GT / Pred")
    gt_list = load_gt_json_dir(gt_dir)
    pred_list = load_pred_csv(pred_csv)
    print(f"  GT: {len(gt_list)}, Pred: {len(pred_list)}")

    print("  Step4: camera")
    cam_data = {name: load_camera_frames_cached(bag_path, topic)
                for name, topic in cfg["CAMERA_TOPICS"].items()}

    main_frames = lidar_data[cfg["LIDAR_CFG_LIST"][0]["topic"]]
    if not main_frames:
        print("  ⚠️ 主雷达帧为空，跳过")
        return False
    gt_match_map = build_gt_match_map(main_frames, gt_list, cfg["GT_MAX_DIFF_MS"])
    print(f"  GT 匹配成功 {sum(g is not None for g in gt_match_map)} 帧")

    print("  Step5: render")
    image_paths = []
    for idx in tqdm(range(len(main_frames)), desc=f"    渲染"):
        t_ms = main_frames[idx]["t_ms"]
        odom = find_nearest_by_time(odom_list, t_ms)
        car_x = odom["T"][0, 3]
        car_y = odom["T"][1, 3]
        car_z = odom["T"][2, 3]
        car_yaw = get_yaw_from_matrix(odom["T"])

        gt_item = gt_match_map[idx]
        pred_item = find_nearest_by_time(pred_list, t_ms) if pred_list else None
        if pred_item and abs(pred_item["t_ms"] - t_ms) > cfg["PRED_MAX_DIFF_MS"]:
            pred_item = None

        pts_rel_list = _collect_points(lidar_data, cfg["LIDAR_CFG_LIST"], t_ms,
                                      odom["T"], car_x, car_y, car_z, car_yaw,
                                      cfg["FRAME_MATCH_MS"])
        gt_view = _transform_gt_to_view(gt_item["data"], odom["T"],
                                       car_x, car_y, car_z, car_yaw) if gt_item else None
        pred_view = _transform_pred_to_view(pred_item, car_x, car_y, car_z, car_yaw) if pred_item else None

        bev_img, _ = render_bev(pts_rel_list, gt_data=gt_view, pred_data=pred_view,
                                view_range=cfg["VIEW_RANGE_BEV"],
                                point_color=cfg["POINT_COLOR"],
                                frame_idx=idx, t_ms=t_ms)
        d3_img, _ = render_3d(pts_rel_list, gt_data=gt_view, pred_data=pred_view,
                              view_x_back=cfg["VIEW_X_BACK"],
                              view_x_front=cfg["VIEW_X_FRONT"],
                              view_y=cfg["VIEW_Y"],
                              view_z_min=cfg["VIEW_Z_MIN"],
                              view_z_max=cfg["VIEW_Z_MAX"],
                              point_color=cfg["POINT_COLOR"],
                              box_center_margin=cfg["BOX_CENTER_MARGIN"],
                              axis_aspect=cfg["AXIS_ASPECT"],
                              elev=cfg["ELEV"], azim=cfg["AZIM"],
                              frame_idx=idx, t_ms=t_ms)
        cam_panel = build_camera_panel(cam_data, t_ms, cfg["CAMERA_MAX_DIFF_MS"],
                                       cfg["CAM_RIGHT_WIDTH"], cfg["CAM_GAP"])

        fusion = np.hstack([
            resize_to_height(bev_img, cfg["TOTAL_HEIGHT"]),
            resize_to_height(d3_img, cfg["TOTAL_HEIGHT"]),
            resize_to_height(cam_panel, cfg["TOTAL_HEIGHT"]),
        ])
        img_path = os.path.join(frames_dir, f"frame_{idx:04d}.png")
        cv2.imwrite(img_path, fusion)
        image_paths.append(img_path)

    print("  Step6: video")
    writer = imageio.get_writer(video_path, fps=cfg["FPS"])
    for img_path in tqdm(image_paths, desc="    合成"):
        writer.append_data(imageio.imread(img_path))
    writer.close()
    print(f"  ✅ {video_path}")
    return True
