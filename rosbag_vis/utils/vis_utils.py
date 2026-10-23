import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


# ========== 2D BEV ==========
def corner2boxes_2d(center_x, center_y, length, width, yaw):
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
    # 启用深色背景
    plt.style.use('dark_background')
    
    fig, ax = plt.subplots(figsize=(10.24, 10.24), dpi=100)
    total_pts = 0

    # 点云
    for pts_rel in pts_rel_list:
        mask = ((pts_rel[:, 0] >= -view_range) & (pts_rel[:, 0] <= view_range) &
                (pts_rel[:, 1] >= -view_range) & (pts_rel[:, 1] <= view_range))
        pts_rel = pts_rel[mask]
        if pts_rel.shape[0] > 0:
            ax.scatter(pts_rel[:, 0], pts_rel[:, 1], s=0.1, c=point_color, alpha=0.6)
            total_pts += pts_rel.shape[0]

    # GT框
    if gt_data is not None and "objects" in gt_data:
        for obj in gt_data["objects"]:
            obj_x, obj_y, _ = obj["translation"]
            w, l, h = obj["size"]
            corners = corner2boxes_2d(obj_x, obj_y, l, w, obj["yaw"])
            corners = np.vstack([corners, corners[0]])
            ax.plot(corners[:, 0], corners[:, 1], '#ff3333', linewidth=1.5)
            ax.text(obj_x, obj_y + w/2 + 1.5, f"GT:{obj['ID']}",
                    fontsize=7, color='#ff6666', ha='center', va='bottom')

    # Pred框
    if pred_data is not None and "objects" in pred_data:
        for obj in pred_data["objects"]:
            obj_x, obj_y, _ = obj["translation"]
            w, l, h = obj["size"]
            corners = corner2boxes_2d(obj_x, obj_y, l, w, obj["yaw"])
            corners = np.vstack([corners, corners[0]])
            ax.plot(corners[:, 0], corners[:, 1], '#33ff66', linewidth=1.2, linestyle='--')
            ax.text(obj_x, obj_y - w/2 - 1.5, f"P:{obj['track_id']}({obj['conf']:.2f})",
                    fontsize=7, color='#66ff99', ha='center', va='top')

    # 自车标识（黑底改白色）
    ax.arrow(0, 0, 8, 0, head_width=3.0, color='white', zorder=10)
    ax.plot(0, 0, 'wo', markersize=8, zorder=10)

    # 坐标轴
    ax.set_xlim(-view_range, view_range)
    ax.set_ylim(-view_range, view_range)
    ax.set_aspect('equal')
    ax.set_xlabel('X (forward, m)', color='white')
    ax.set_ylabel('Y (left, m)', color='white')
    ax.set_title(f'FRAME {frame_idx:04d}  timestamp={t_ms}ms  x={car_x:.1f}  y={car_y:.1f}', color='white')
    
    # 网格改成浅灰色
    ax.grid(True, alpha=0.2, color='#666666')
    
    # 刻度改成白色
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    # 保存时强制黑色背景
    if save_path:
        plt.savefig(save_path, dpi=100, facecolor='black')
    plt.close()
    return total_pts



# ========== 3D View ==========
def corner2boxes_3d(center_x, center_y, center_z, length, width, height, yaw):
    bottom = corner2boxes_2d(center_x, center_y, length, width, yaw)
    corners_3d = np.vstack([
        np.hstack([bottom, np.zeros((4, 1))]),
        np.hstack([bottom, np.full((4, 1), height)])
    ])
    corners_3d[:, 2] += center_z - height/2
    return corners_3d


def draw_3d_box(ax, corners_3d, color='r', linestyle='-', linewidth=1.0, alpha=0.4):
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


def _filter_boxes_by_center(obj_list, x_min, x_max, y_min, y_max, z_min, z_max, margin):
    """按中心点+冗余过滤框，边缘超范围也保留整框"""
    filtered = []
    for obj in obj_list:
        x, y, z = obj["translation"]
        if x < x_min - margin[0] or x > x_max + margin[0]:
            continue
        if y < y_min - margin[1] or y > y_max + margin[1]:
            continue
        if z < z_min - margin[2] or z > z_max + margin[2]:
            continue
        filtered.append(obj)
    return filtered


def draw_3d_frame(
    pts_rel_list,
    view_x_back=20.0, view_x_front=50.0, view_y=30.0,
    view_z_min=-2.0, view_z_max=8.0,
    point_color='#48D1CC', point_size=0.1, point_alpha=1.0,
    frame_idx=0, t_ms=0,
    gt_data=None, pred_data=None,
    gt_color='#ff3333', pred_color='#33ff66',
    box_linewidth=1.0, box_alpha=0.35,
    box_center_margin=(5.0, 5.0, 2.0),
    axis_aspect=(1, 1.5, 0.8),
    elev=60.0, azim=180.0,
    show_grid=False, show_panes=False,
    figsize=(16, 10), dpi=150,
    save_path=None
):
    """统一3D绘图入口：点云+GT+Pred，带所有视觉优化"""
    plt.style.use('dark_background')   # 加这一行
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(111, projection='3d')
    total_pts = 0

    # 画点云
    for pts_rel in pts_rel_list:
        mask = (
            (pts_rel[:, 0] >= -view_x_back) & (pts_rel[:, 0] <= view_x_front) &
            (pts_rel[:, 1] >= -view_y) & (pts_rel[:, 1] <= view_y) &
            (pts_rel[:, 2] >= view_z_min) & (pts_rel[:, 2] <= view_z_max)
        )
        pts = pts_rel[mask]
        if pts.shape[0] > 0:
            ax.scatter(pts[:, 0], pts[:, 1], pts[:, 2],
                       s=point_size, c=point_color, alpha=point_alpha)
            total_pts += pts.shape[0]

    # 画GT框
    if gt_data is not None and "objects" in gt_data:
        gt_objs = _filter_boxes_by_center(
            gt_data["objects"],
            -view_x_back, view_x_front, -view_y, view_y, view_z_min, view_z_max,
            box_center_margin
        )
        for obj in gt_objs:
            x, y, z = obj["translation"]
            w, l, h = obj["size"]
            corners = corner2boxes_3d(x, y, z, l, w, h, obj["yaw"])
            draw_3d_box(ax, corners, color=gt_color, linestyle='-',
                        linewidth=box_linewidth, alpha=box_alpha)

    # 画Pred框
    if pred_data is not None and "objects" in pred_data:
        pred_objs = _filter_boxes_by_center(
            pred_data["objects"],
            -view_x_back, view_x_front, -view_y, view_y, view_z_min, view_z_max,
            box_center_margin
        )
        for obj in pred_objs:
            x, y, z = obj["translation"]
            w, l, h = obj["size"]
            corners = corner2boxes_3d(x, y, z, l, w, h, obj["yaw"])
            draw_3d_box(ax, corners, color=pred_color, linestyle='--',
                        linewidth=box_linewidth, alpha=box_alpha)

    # 坐标轴
    ax.set_xlim(-view_x_back, view_x_front)
    ax.set_ylim(-view_y, view_y)
    ax.set_zlim(view_z_min, view_z_max)
    ax.set_box_aspect(axis_aspect)

    ax.set_xlabel('X (forward, m)', fontsize=12)
    ax.set_ylabel('Y (left, m)', fontsize=12)
    ax.set_zlabel('Z (up, m)', fontsize=12)
    ax.set_title(f'3D Global + GT + Pred - FRAME {frame_idx:04d}  t={t_ms}ms', fontsize=14)

    # 视角与视觉优化
    ax.view_init(elev=elev, azim=azim)
    ax.grid(show_grid)
    ax.xaxis.pane.set_visible(show_panes)
    ax.yaxis.pane.set_visible(show_panes)
    ax.zaxis.pane.set_visible(show_panes)

    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight', facecolor='black')
    plt.close()
    return total_pts
