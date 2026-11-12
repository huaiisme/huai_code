# rosbag_vis

rosbag 点云 / GT / Pred / 相机的离线可视化包。

## 目录结构

```
rosbag_vis/
├── 3view_fusion.py                 # 入口（批量）：枚举 bag → 逐 bag 跑 BEV+3D+相机 → mp4
├── 2d_view_world_with_gt_pred.py  # 入口：纯 BEV（GT+Pred）→ 视频
├── 3d_view_world_with_gt_pred.py   # 入口：纯 3D（GT+Pred）→ 视频
├── selftest.py                     # 无 bag 的渲染自检（合成数据）
├── utils/
│   ├── tf.py                       # 4x4 变换矩阵构造/解析、transform_points
│   ├── geometry.py                 # 世界系↔自车视角、GT/Pred 框两端变换
│   └── image.py                    # fig↔cv2、缩放、面板标签
└── tools/
    ├── bag_reader/
    │   ├── base.py                 # 缓存、时间最近邻、odom、GT JSON、Pred CSV
    │   ├── lidar.py                # 点云帧读取（带缓存）
    │   └── camera.py               # 相机帧读取（带缓存，bgr8）
    ├── vis/
    │   ├── bev.py                  # BEV 俯视图渲染
    │   ├── lidar_3d.py             # 3D 点云视图渲染
    │   └── camera_panel.py         # 右侧三相机纵向面板
    └── pipeline.py                 # 批量 runner：discover_bags + run_one_bag
```

## 运行

进入本目录后直接运行对应入口脚本（依赖 rosbag / sensor_msgs / cv_bridge，需 ROS 环境）：

```bash
python 3view_fusion.py                 # 批量：扫 BAG_ROOTS 下所有 .bag，自动匹配 GT/Pred
python 2d_view_world_with_gt_pred.py  # 单 bag
python 3d_view_world_with_gt_pred.py    # 单 bag
```

无 bag 时先跑渲染自检：

```bash
python selftest.py    # 生成 selftest_bev.png / selftest_3d.png
```

## 批量配置（3view_fusion.py 顶部）

```python
DATA_ROOT = "/home/huai/huai_work/data"
BAG_ROOTS = [f"{DATA_ROOT}/eval_260609before"]   # 可加第二个目录
GT_ROOT   = f"{DATA_ROOT}/gt_label_simple"        # 调试期；正式切 gt_label
PRED_ROOT = f"{DATA_ROOT}/pred_simple"            # 调试期；正式切 pred
```

- 自动扫描 `BAG_ROOTS` 下所有 `*.bag`，按 bag 名自动拼 `GT_ROOT/{bag名}/` 和 `PRED_ROOT/{bag名}.csv`。
- 缺 GT 目录的 bag 自动跳过并计数。
- 输出落到 `./batch_3view_out/{bag名}/frames/*.png` + `{bag名}.mp4`，互不污染。
- 缓存仍由 `tools/bag_reader/base.py` 自动落在 bag 同级 `{bag名}_cache/`，多 bag 零冲突。

## 坐标变换约定

- 点云链路：`lidar 系 --T_lidar--> 自车系 --odom_T--> 世界系 --world_to_ego_view--> 自车视角`
- GT 框在自车系给出：`box_ego_to_world` 进世界系，再 `box_world_to_ego_view` 回视角
- Pred 框在世界系给出：直接 `box_world_to_ego_view`
- 2D BEV 用 `world_to_ego_view_2d`（Z 不动），3D 视图用 `world_to_ego_view_3d`（Z 对齐自车）
