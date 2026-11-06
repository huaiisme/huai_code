import numpy as np
import cv2
from my_nuscenes import MyNuScenes

# ========== 配置项 ==========
NUSCENES_ROOT = "/mnt/Ddisk/data/nuscenes"
VERSION = "v1.0-mini"
SAMPLE_IDX = 0          # 取第几个关键帧
CAM_NAME = "CAM_FRONT"  # 指定相机
POINT_RADIUS = 3
MAX_DEPTH = 80.0
# ============================

def quaternion_to_rotation_matrix(q):
    """
    自研：四元数转3x3旋转矩阵
    输入: q = [w, x, y, z] （nuScenes的四元数顺序是wxyz）
    输出: 3x3 旋转矩阵
    """
    w, x, y, z = q
    rot = np.array([
        [1 - 2*y*y - 2*z*z,  2*x*y - 2*z*w,    2*x*z + 2*y*w],
        [2*x*y + 2*z*w,      1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w],
        [2*x*z - 2*y*w,      2*y*z + 2*x*w,    1 - 2*x*x - 2*y*y]
    ], dtype=np.float32)
    return rot




def main():
    # 1. 初始化自研数据集类（加载所有标注元数据到内存）
    nusc = MyNuScenes(version=VERSION, dataroot=NUSCENES_ROOT, verbose=True)

    # 2. 取出第 SAMPLE_IDX 帧关键帧的元信息
    sample = nusc.sample[SAMPLE_IDX]
    print(f"\n===== 第 {SAMPLE_IDX} 帧关键帧信息 =====")
    print(f"帧唯一token: {sample['token']}")
    print(f"时间戳: {sample['timestamp']}")
    print(f"包含的传感器: {list(sample['data'].keys())}")
    print(f"本帧标注框数量: {len(sample['anns'])}")

    # ========== 下面是新增的第三步、第四步 ==========

    # 3. 拿到相机和激光雷达对应的 sample_data token
    cam_token = sample["data"][CAM_NAME]
    lidar_token = sample["data"]["LIDAR_TOP"]
    print(f"\n===== 传感器token =====")
    print(f"前视相机token: {cam_token}")
    print(f"顶部激光雷达token: {lidar_token}")

    # 4. 获取文件的本地绝对路径
    cam_path = nusc.get_sample_data_path(cam_token)
    lidar_path = nusc.get_sample_data_path(lidar_token)
    print(f"\n===== 文件路径 =====")
    print(f"相机图像: {cam_path}")
    print(f"激光点云: {lidar_path}")

    # 5. 读取相机图像到内存
    img = cv2.imread(cam_path)
    print(f"\n===== 图像读取结果 =====")
    print(f"尺寸: 宽{img.shape[1]} × 高{img.shape[0]} × 通道{img.shape[2]}")
    print(f"像素值范围: {img.min()} ~ {img.max()}")

    # 6. 读取激光点云到内存
    points_raw = np.fromfile(lidar_path, dtype=np.float32)
    points = points_raw.reshape(-1, 5)  # 每个点固定5个维度：x,y,z,intensity,ring
    print(f"\n===== 点云读取结果 =====")
    print(f"总点数: {points.shape[0]}")
    print(f"x坐标范围: {points[:,0].min():.2f} ~ {points[:,0].max():.2f} 米（雷达坐标系）")
    print(f"y坐标范围: {points[:,1].min():.2f} ~ {points[:,1].max():.2f} 米")
    print(f"z坐标范围: {points[:,2].min():.2f} ~ {points[:,2].max():.2f} 米")
    print(f"强度范围: {points[:,3].min():.2f} ~ {points[:,3].max():.2f}")

    # 7. 获取传感器标定参数（外参+内参，坐标变换的核心）
    # 先查sample_data详情，拿到calibrated_sensor的token
    cam_sd = nusc.get("sample_data", cam_token)
    cs_token = cam_sd["calibrated_sensor_token"]
    # 再查calibrated_sensor表，拿到标定参数
    cam_calib = nusc.get("calibrated_sensor", cs_token)
    print(f"\n===== 相机标定参数 =====")
    print(f"外参平移(相对自车): {cam_calib['translation']}  单位：米")
    print(f"外参旋转(四元数): {cam_calib['rotation']}")
    print(f"相机内参矩阵:\n{np.array(cam_calib['camera_intrinsic'])}")

    # 同理拿激光雷达的标定参数
    lidar_sd = nusc.get("sample_data", lidar_token)
    lidar_calib = nusc.get("calibrated_sensor", lidar_sd["calibrated_sensor_token"])
    print(f"\n===== 激光雷达标定参数 =====")
    print(f"外参平移(相对自车): {lidar_calib['translation']}  单位：米")
    print(f"外参旋转(四元数): {lidar_calib['rotation']}")

    print("\n✅ 单帧数据+标定参数读取完成，可直接用于后续坐标变换")

    # 取出两个传感器的详情
    cam_sd = nusc.get("sample_data", cam_token)
    lidar_sd = nusc.get("sample_data", lidar_token)

    print(f"当前sample的token: {sample['token']}")
    print(f"相机数据的sample_token: {cam_sd['sample_token']}")
    print(f"激光数据的sample_token: {lidar_sd['sample_token']}")
    print(f"三者是否一致: {sample['token'] == cam_sd['sample_token'] == lidar_sd['sample_token']}")





if __name__ == "__main__":
    main()