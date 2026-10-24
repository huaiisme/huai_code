"""BEV 俯视图渲染（点云 + GT/Pred 2D 框）。"""
import matplotlib
matplotlib.use("Agg")  # 无头/服务器安全
import matplotlib.pyplot as plt
import numpy as np

from utils.image import fig_to_cv2


def corner2boxes_2d(center_x, center_y, length, width, yaw):
    """自车视角下由中心/尺寸/yaw 求矩形 4 个角点（Nx2）。"""
    corners = np.array([
        [ length / 2,  width / 2],
        [-length / 2,  width / 2],
        [-length / 2, -width / 2],
        [ length / 2, -width / 2],
    ])
    c, s = np.cos(yaw), np.sin(yaw)
    R = np.array([[c, -s], [s, c]])
    corners = (R @ corners.T).T
    corners[:, 0] += center_x
    corners[:, 1] += center_y
    return corners


def _closed(corners):
    """把 4 角点闭合为 5 个点（首尾相同），矩形才会画出第 4 条边。"""
    return np.vstack([corners, corners[0]])


def _draw_boxes_2d(ax, gt_data, pred_data, show_labels):
    if gt_data and gt_data.get("objects"):
        for obj in gt_data["objects"]:
            x, y, _ = obj["translation"]
            w, l, _ = obj["size"]
            corners = _closed(corner2boxes_2d(x, y, l, w, obj["yaw"]))
            ax.plot(corners[:, 0], corners[:, 1], color="#ff3333", linewidth=1.5)
            if show_labels:
                ax.text(x, y + w / 2 + 1.5, f"GT:{obj['ID']}", fontsize=7,
                        color="#ff6666", ha="center", va="bottom")
    if pred_data and pred_data.get("objects"):
        for obj in pred_data["objects"]:
            x, y, _ = obj["translation"]
            w, l, _ = obj["size"]
            corners = _closed(corner2boxes_2d(x, y, l, w, obj["yaw"]))
            ax.plot(corners[:, 0], corners[:, 1], color="#33ff66",
                    linestyle="--", linewidth=1.2)
            if show_labels:
                ax.text(x, y - w / 2 - 1.5, f"P:{obj['track_id']}({obj['conf']:.2f})",
                        fontsize=7, color="#66ff99", ha="center", va="top")


def render_bev(pts_rel_list, gt_data=None, pred_data=None, view_range=100.0,
               point_color="#48D1CC", frame_idx=0, t_ms=0,
               show_labels=False, car_x=None, car_y=None,
               figsize=(8, 8), dpi=120):
    """渲染一帧 BEV，返回 (BGR ndarray, 落在视野内的点数量)。"""
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    total_pts = 0

    for pts in pts_rel_list:
        mask = ((pts[:, 0] >= -view_range) & (pts[:, 0] <= view_range) &
                (pts[:, 1] >= -view_range) & (pts[:, 1] <= view_range))
        pts = pts[mask]
        if pts.shape[0]:
            ax.scatter(pts[:, 0], pts[:, 1], s=0.1, c=point_color, alpha=0.6)
            total_pts += pts.shape[0]

    _draw_boxes_2d(ax, gt_data, pred_data, show_labels)

    ax.arrow(0, 0, 8, 0, head_width=3.0, color="white", zorder=10)
    ax.plot(0, 0, "wo", markersize=8, zorder=10)
    ax.set_xlim(-view_range, view_range)
    ax.set_ylim(-view_range, view_range)
    ax.set_aspect("equal")
    ax.set_xlabel("X (forward, m)", color="white", fontsize=8)
    ax.set_ylabel("Y (left, m)", color="white", fontsize=8)
    if show_labels and car_x is not None:
        title = f"FRAME {frame_idx:04d}  timestamp={t_ms}ms  x={car_x:.1f}  y={car_y:.1f}"
    else:
        title = f"BEV - FRAME {frame_idx:04d}"
    ax.set_title(title, color="white", fontsize=9)
    ax.grid(True, alpha=0.15, color="#666666")
    ax.tick_params(colors="white", labelsize=7)
    plt.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)

    img = fig_to_cv2(fig)
    plt.close(fig)
    return img, total_pts


def draw_bev_frame(pts_rel_list, car_x, car_y, yaw=None, view_range=100.0,
                   point_color="#48D1CC", frame_idx=0, t_ms=0,
                   gt_data=None, pred_data=None, save_path=None):
    """2D 视图脚本入口：渲染并写盘，返回点数量。yaw 仅为兼容旧调用。"""
    img, total_pts = render_bev(
        pts_rel_list, gt_data=gt_data, pred_data=pred_data,
        view_range=view_range, point_color=point_color,
        frame_idx=frame_idx, t_ms=t_ms, show_labels=True,
        car_x=car_x, car_y=car_y, figsize=(10.24, 10.24), dpi=100)
    if save_path:
        import cv2
        cv2.imwrite(save_path, img)
    return total_pts
