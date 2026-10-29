"""三视角融合批量渲染：BEV + 3D + 右侧三相机面板 → 每 bag 一个 mp4。

调试期：GT_ROOT/PRED_ROOT 指向 *_simple（只跑有 GT 的 2 个示例 bag）。
跑通后：把 GT_ROOT/PRED_ROOT 切回 gt_label/pred，并按需打开第二个 BAG_ROOT。

运行方式：进入本目录后执行 python 3view_fusion.py
"""
import os

from utils.tf import create_tf_matrix
from tools.pipeline import discover_bags, run_one_bag

# ===================== 根路径（调试期 → simple） =====================
DATA_ROOT = "/home/huai/huai_work/data"
BAG_ROOTS = [
    # f"{DATA_ROOT}/eval_260609before",
    # f"{DATA_ROOT}/eval_260610after",   # 第二批，需要时打开
    f"{DATA_ROOT}/eval_260613after"
]
GT_ROOT = f"{DATA_ROOT}/gt_label"     # 调试期；正式切到 gt_label
PRED_ROOT = f"{DATA_ROOT}/pred"       # 调试期；正式切到 pred

ODOM_TOPIC = "/gps/odom"

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
VIEW_X_FRONT = 50.0
VIEW_X_BACK = 20.0
VIEW_Y = 30.0
VIEW_Z_MIN = -2.0
VIEW_Z_MAX = 8.0
BOX_CENTER_MARGIN = (5.0, 5.0, 2.0)
AXIS_ASPECT = (1, 1.5, 0.8)
ELEV = 60.0
AZIM = 180.0

# 时间匹配阈值 (ms)
GT_MAX_DIFF_MS = 150
PRED_MAX_DIFF_MS = 150
FRAME_MATCH_MS = 50
CAMERA_MAX_DIFF_MS = 100

# 输出
TOTAL_HEIGHT = 900
CAM_RIGHT_WIDTH = 540
CAM_GAP = 0
OUTPUT_ROOT = "./batch_3view_out"
FPS = 10


def build_cfg():
    """把外参一次性 bake 进 LIDAR_CFG_LIST（车固，不随 bag 变）。"""
    for c in LIDAR_CFG_LIST:
        c["T_lidar"] = create_tf_matrix(c["tf_xyz"], c["tf_rpy"])
    return {
        "ODOM_TOPIC": ODOM_TOPIC,
        "CAMERA_TOPICS": CAMERA_TOPICS,
        "LIDAR_CFG_LIST": LIDAR_CFG_LIST,
        "POINT_COLOR": POINT_COLOR,
        "VIEW_RANGE_BEV": VIEW_RANGE_BEV,
        "VIEW_X_BACK": VIEW_X_BACK,
        "VIEW_X_FRONT": VIEW_X_FRONT,
        "VIEW_Y": VIEW_Y,
        "VIEW_Z_MIN": VIEW_Z_MIN,
        "VIEW_Z_MAX": VIEW_Z_MAX,
        "BOX_CENTER_MARGIN": BOX_CENTER_MARGIN,
        "AXIS_ASPECT": AXIS_ASPECT,
        "ELEV": ELEV,
        "AZIM": AZIM,
        "GT_MAX_DIFF_MS": GT_MAX_DIFF_MS,
        "PRED_MAX_DIFF_MS": PRED_MAX_DIFF_MS,
        "FRAME_MATCH_MS": FRAME_MATCH_MS,
        "CAMERA_MAX_DIFF_MS": CAMERA_MAX_DIFF_MS,
        "TOTAL_HEIGHT": TOTAL_HEIGHT,
        "CAM_RIGHT_WIDTH": CAM_RIGHT_WIDTH,
        "CAM_GAP": CAM_GAP,
        "OUTPUT_ROOT": OUTPUT_ROOT,
        "FPS": FPS,
    }


def main():
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    tasks = discover_bags(BAG_ROOTS, GT_ROOT, PRED_ROOT)
    print(f"共 {len(tasks)} 个待处理 bag:")
    for t in tasks:
        print(f"  - {os.path.basename(t['bag_path'])}")

    cfg = build_cfg()
    ok, fail = 0, 0
    for t in tasks:
        try:
            run_one_bag(t["bag_path"], t["gt_dir"], t["pred_csv"], cfg)
            ok += 1
        except Exception as e:
            fail += 1
            print(f"❌ {os.path.basename(t['bag_path'])} 失败: {e}")
    print(f"\n==== 批量完成: 成功 {ok}, 失败 {fail} ====")


if __name__ == "__main__":
    main()
