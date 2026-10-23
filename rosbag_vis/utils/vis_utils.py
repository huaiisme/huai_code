import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # ← 加这一行，注册3D投影

# ========== 2D BEV ==========
def corner2boxes_2d(center_x, center_y, length, width, yaw):
    """BEV 2D包围盒：中心+长宽+航向 → 4个角点"""
    corners = np.array([
        [ length/2,  width/2],
        [-length/2,  width/2],
        [-length/2, -width/2],
        [ length/2, -width/2],
    ])
    cos_y, sin_y = np.cos(yaw), np.sin(yaw)
    R = np.array([[cos_y, -sin_y], [sin_y, cos_y]])
    corners = (R @ corners.T).T
    corners[:, 0] += center_x
    corners[:, 1] += center_y
    return corners


def draw_bev_frame(pts_rel_list, car_x, car_y, yaw,
                   view_range=100.0, point_color='#4A0072',
                   frame_idx=0, t_ms=0, gt_data=None, pred_data=None, save_path=None):
    """画2D BEV图"""
    fig, ax = plt.subplots(figsize=(10.24, 10.24), dpi=100)
    total_pts = 0

    for pts_rel in pts_rel_list:
        mask = ((pts_rel[:, 0] >= -view_range) & (pts_rel[:, 0] <= view_range) &
                (pts_rel[:, 1] >= -view_range) & (pts_rel[:, 1] <= view_range))
        pts_rel = pts_rel[mask]
        if pts_rel.shape[0] > 0:
            ax.scatter(pts_rel[:, 0], pts_rel[:, 1],
                       s=0.1, c=point_color, alpha=0.6)
            total_pts += pts_rel.shape[0]

    if gt_data is not None and "objects" in gt_data:
        for obj in gt_data["objects"]:
            obj_x, obj_y, _ = obj["translation"]
            w, l, h = obj["size"]
            corners = corner2boxes_2d(obj_x, obj_y, l, w, obj["yaw"])
            corners = np.vstack([corners, corners[0]])
            ax.plot(corners[:, 0], corners[:, 1], 'r-', linewidth=1.5)
            ax.text(obj_x, obj_y + w/2 + 1.5, f"GT:{obj['ID']}",
                    fontsize=7, color='red', ha='center', va='bottom')

    if pred_data is not None and "objects" in pred_data:
        for obj in pred_data["objects"]:
            obj_x, obj_y, _ = obj["translation"]
            w, l, h = obj["size"]
            corners = corner2boxes_2d(obj_x, obj_y, l, w, obj["yaw"])
            corners = np.vstack([corners, corners[0]])
            ax.plot(corners[:, 0], corners[:, 1], 'g--', linewidth=1.2)
            ax.text(obj_x, obj_y - w/2 - 1.5, f"P:{obj['track_id']}({obj['conf']:.2f})",
                    fontsize=7, color='green', ha='center', va='top')

    ax.arrow(0, 0, 8, 0, head_width=3.0, color='black', zorder=10)
    ax.plot(0, 0, 'ko', markersize=8, zorder=10)
    ax.set_xlim(-view_range, view_range)
    ax.set_ylim(-view_range, view_range)
    ax.set_aspect('equal')
    ax.set_xlabel('X (forward, m)')
    ax.set_ylabel('Y (left, m)')
    ax.set_title(f'FRAME {frame_idx:04d}  timestamp={t_ms}ms  x={car_x:.1f}  y={car_y:.1f}')
    ax.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=100)
    plt.close()
    return total_pts


# ========== 3D View ==========
def corner2boxes_3d(center_x, center_y, center_z, length, width, height, yaw):
    """3D包围盒：中心+长宽高+航向 → 8个角点"""
    bottom = corner2boxes_2d(center_x, center_y, length, width, yaw)
    corners_3d = np.vstack([
        np.hstack([bottom, np.zeros((4, 1))]),
        np.hstack([bottom, np.full((4, 1), height)])
    ])
    corners_3d[:, 2] += center_z - height/2
    return corners_3d

def draw_3d_box(ax, corners_3d, color='r', linestyle='-', linewidth=1.0, alpha=0.4):
    """3D包围盒线框，保持原始纯线框样式，仅降低透明度"""
    edges = [
        [0, 1], [1, 2], [2, 3], [3, 0],
        [4, 5], [5, 6], [6, 7], [7, 4],
        [0, 4], [1, 5], [2, 6], [3, 7],
    ]

    for i, j in edges:
        ax.plot([corners_3d[i, 0], corners_3d[j, 0]],
                [corners_3d[i, 1], corners_3d[j, 1]],
                [corners_3d[i, 2], corners_3d[j, 2]],
                color=color, linestyle=linestyle,
                linewidth=linewidth, alpha=alpha)



def draw_3d_frame(pts_rel_list, car_x, car_y, yaw,
                   view_range=100.0, point_color='#4A0072',
                   frame_idx=0, t_ms=0, gt_data=None, pred_data=None,
                   elev=60.0, azim=-90.0, save_path=None):
    """画3D视角BEV图"""
    fig = plt.figure(figsize=(12, 10), dpi=100)
    ax = fig.add_subplot(111, projection='3d')
    total_pts = 0

    # 点云
    for pts_rel in pts_rel_list:
        mask = ((pts_rel[:, 0] >= -view_range) & (pts_rel[:, 0] <= view_range) &
                (pts_rel[:, 1] >= -view_range) & (pts_rel[:, 1] <= view_range))
        pts_rel = pts_rel[mask]
        if pts_rel.shape[0] > 0:
            ax.scatter(pts_rel[:, 0], pts_rel[:, 1], pts_rel[:, 2],
                       s=0.1, c=point_color, alpha=0.6)
            total_pts += pts_rel.shape[0]

    # GT框（红色实线）
    if gt_data is not None and "objects" in gt_data:
        for obj in gt_data["objects"]:
            x, y, z = obj["translation"]
            w, l, h = obj["size"]
            corners_3d = corner2boxes_3d(x, y, z, l, w, h, obj["yaw"])
            draw_3d_box(ax, corners_3d, color='r', linestyle='-', linewidth=1.5)

    # Pred框（绿色虚线）
    if pred_data is not None and "objects" in pred_data:
        for obj in pred_data["objects"]:
            x, y, z = obj["translation"]
            w, l, h = obj["size"]
            corners_3d = corner2boxes_3d(x, y, z, l, w, h, obj["yaw"])
            draw_3d_box(ax, corners_3d, color='g', linestyle='--', linewidth=1.2)

    ax.set_xlim(-view_range, view_range)
    ax.set_ylim(-view_range, view_range)
    ax.set_zlim(-5, 15)
    ax.set_xlabel('X (forward, m)')
    ax.set_ylabel('Y (left, m)')
    ax.set_zlabel('Z (up, m)')
    ax.set_title(f'3D View - FRAME {frame_idx:04d}  t={t_ms}ms  elev={elev}°')
    ax.view_init(elev=elev, azim=azim)

    if save_path:
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
    plt.close()
    return total_pts
