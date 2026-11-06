# Data Preparation

## Nuscenes mini 数据调试
```{code-block} shell
:linenos:
:caption: Nuscenes mini 数据调试
1. 去 nuScenes 官网注册账号，下载 `v1.0-mini.tgz`
2. 解压到你的数据盘，比如 `/mnt/Ddisk/data/nuscenes/`
3. 解压后目录结构必须长这样：
/mnt/Ddisk/data/nuscenes/
├── samples/       # 关键帧（6相机图像 + LiDAR点云）
├── sweeps/        # 中间帧
├── maps/          # 地图文件
└── v1.0-mini/     # 标注与标定文件（json）
tar -zxvf v1.0-mini.tgz

```

