"""3D 点云视图渲染（点云 + GT/Pred 3D 框）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from utils.image import fig_to_cv2
from tools.vis.bev import corner2boxes_2d

_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0),
          (4, 5), (5, 6), (6, 7), (7, 4),
          (0, 4), (1, 5), (2, 6), (3, 7)]


def corner2boxes_3d(center_x, center_y, center_z, length, width, height, yaw):
    """由中心/尺寸/yaw 求 3D 框 8 个角点（Nx3，0~3 底、4~7 顶）。"""
    bottom = corner2boxes_2d(center_x, center_y, length, width, yaw)
    corners = np.vstack([
        np.hstack([bottom, np.zeros((4, 1))]),
        np.hstack([bottom, np.full((4, 1), height)]),
    ])
    corners[:, 2] += center_z - height / 2
    return corners


def draw_3d_box(ax, corners_3d, color="r", linestyle="-", linewidth=1.0, alpha=0.4):
    for i, j in _EDGES:
        ax.plot([corners_3d[i, 0], corners_3d[j, 0]],
                [corners_3d[i, 1], corners_3d[j, 1]],
                [corners_3d[i, 2], corners_3d[j, 2]],
                color=color, linestyle=linestyle,
                linewidth=linewidth, alpha=alpha)


def _filter_boxes(obj_list, x_min, x_max, y_min, y_max, z_min, z_max, margin):
    out = []
    for obj in obj_list:
        x, y, z = obj["translation"]
        if not (x_min - margin[0] <= x <= x_max + margin[0]):
            continue
        if not (y_min - margin[1] <= y <= y_max + margin[1]):
            continue
        if not (z_min - margin[2] <= z <= z_max + margin[2]):
            continue
        out.append(obj)
    return out


def _draw_boxes_3d(ax, gt_data, pred_data, view_x_back, view_x_front, view_y,
                   view_z_min, view_z_max, margin):
    lo = (-view_x_back, -view_y, view_z_min)
    hi = (view_x_front, view_y, view_z_max)
    if gt_data and gt_data.get("objects"):
        for obj in _filter_boxes(gt_data["objects"], lo[0], hi[0], lo[1], hi[1],
                                 lo[2], hi[2], margin):
            x, y, z = obj["translation"]
            w, l, h = obj["size"]
            draw_3d_box(ax, corner2boxes_3d(x, y, z, l, w, h, obj["yaw"]),
                        color="#ff3333", linestyle="-", linewidth=1.0, alpha=0.35)
    if pred_data and pred_data.get("objects"):
        for obj in _filter_boxes(pred_data["objects"], lo[0], hi[0], lo[1], hi[1],
                                 lo[2], hi[2], margin):
            x, y, z = obj["translation"]
            w, l, h = obj["size"]
            draw_3d_box(ax, corner2boxes_3d(x, y, z, l, w, h, obj["yaw"]),
                        color="#33ff66", linestyle="--", linewidth=1.0, alpha=0.4)


def render_3d(pts_rel_list, gt_data=None, pred_data=None,
              view_x_back=20.0, view_x_front=50.0, view_y=30.0,
              view_z_min=-2.0, view_z_max=8.0, point_color="#48D1CC",
              box_center_margin=(5.0, 5.0, 2.0), axis_aspect=(1, 1.5, 0.8),
              elev=60.0, azim=180.0, frame_idx=0, t_ms=0,
              figsize=(8, 8), dpi=120, detailed_title=False):
    """渲染一帧 3D 视图，返回 (BGR ndarray, 落在视野内的点数量)。"""
    plt.style.use("dark_background")
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(111, projection="3d")
    total_pts = 0

    for pts in pts_rel_list:
        mask = ((pts[:, 0] >= -view_x_back) & (pts[:, 0] <= view_x_front) &
                (pts[:, 1] >= -view_y) & (pts[:, 1] <= view_y) &
                (pts[:, 2] >= view_z_min) & (pts[:, 2] <= view_z_max))
        pts = pts[mask]
        if pts.shape[0]:
            ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2], s=0.1,
                       c=point_color, alpha=1.0)
            total_pts += pts.shape[0]

    _draw_boxes_3d(ax, gt_data, pred_data, view_x_back, view_x_front, view_y,
                   view_z_min, view_z_max, box_center_margin)

    ax.set_xlim(-view_x_back, view_x_front)
    ax.set_ylim(-view_y, view_y)
    ax.set_zlim(view_z_min, view_z_max)
    ax.set_box_aspect(axis_aspect)
    ax.set_xlabel("X (forward, m)", fontsize=8, color="white")
    ax.set_ylabel("Y (left, m)", fontsize=8, color="white")
    ax.set_zlabel("Z (up, m)", fontsize=8, color="white")
    title = (f"3D EGO + GT + Pred - FRAME {frame_idx:04d}  t={t_ms}ms"
             if detailed_title else f"3D View - FRAME {frame_idx:04d}")
    ax.set_title(title, fontsize=10, color="white")
    ax.tick_params(colors="white", labelsize=7)
    ax.view_init(elev=elev, azim=azim)
    ax.grid(False)
    ax.xaxis.pane.set_visible(False)
    ax.yaxis.pane.set_visible(False)
    ax.zaxis.pane.set_visible(False)
    plt.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)

    img = fig_to_cv2(fig)
    plt.close(fig)
    return img, total_pts


def draw_3d_frame(pts_rel_list, view_x_back=20.0, view_x_front=50.0, view_y=30.0,
                  view_z_min=-2.0, view_z_max=8.0, point_color="#48D1CC",
                  gt_data=None, pred_data=None,
                  box_center_margin=(5.0, 5.0, 2.0), axis_aspect=(1, 1.5, 0.8),
                  elev=60.0, azim=180.0, frame_idx=0, t_ms=0, save_path=None):
    """3D 视图脚本入口：渲染并写盘，返回点数量。"""
    img, total_pts = render_3d(
        pts_rel_list, gt_data=gt_data, pred_data=pred_data,
        view_x_back=view_x_back, view_x_front=view_x_front, view_y=view_y,
        view_z_min=view_z_min, view_z_max=view_z_max, point_color=point_color,
        box_center_margin=box_center_margin, axis_aspect=axis_aspect,
        elev=elev, azim=azim, frame_idx=frame_idx, t_ms=t_ms,
        figsize=(16, 10), dpi=150, detailed_title=True)
    if save_path:
        import cv2
        cv2.imwrite(save_path, img)
    return total_pts
