# ROS1 
就按照以前的搞法弄ros1 后续的话，可能会用QT的方式来启动ros1使用图形UI界面

## 后融合启动命令概览
需要打开以下几个窗口(以下命令为概览非实际运行命令):
```{code-block} shell
:linenos:
:caption: 后融合运行步骤概览
:name: code-block_postfusion run step overview 
# win1 启动roscore
roscore
# win2 播包
rosbag play ***
# win3 车型配置
./xxx/local_env_depoly.sh
# win4 感知启动
./xxx/local_env_run.sh
# win5 可视化
./xxx/run_debug_display.sh
# winX 某些模块单独，例如:
rostopic list
rostopic echo
roslaunch perception_lidar_detection perception_lidar_detection.launch
```

:::{admonition} 流程概览说明
:class: danger
上面代码块为伪代码，用于理清启动顺序，详细命令见后文
:::

### 自启动命令 & 环境编译 
#### 自启动命令: ros-go & start-ros-proj
使用自启动命令：`ros-go`与`start-ros-proj`（相关说明见：{numref}`代码{number}({name})<code-block_ros-go update>` & {numref}`代码{number}({name})<code-block_start-ros-proj update>`）
<!-- <span class="mark-text"> -->

```{code-block} shell
:linenos:
:caption: 后融合代码环境前置
:name: code-block_general_use_local_env_run_reproduce
# 仅启用ros-go的时候，类似roscore, rosplay之类的
ros-go
# 涉及到感知环境相关
start-ros-proj
```

```{code-block} shell
:linenos:
:caption: 感知环境编译
:name: code-block_catkin_make install
cd /work/huai_work/XCMG_work/MultiSensorPostFusion/catkin_ws

# 1. 清缓存（必须，旧配置会残留）
rm -rf build devel install
start-ros-proj
# 2将ads_env下载，另外由于存在模型的问题，我这边是需要从网址下载，不然的话会少onnx & engine
修改脚本中的ros相应路径
# 3. 编译，
catkin_make install -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DCATKIN_WHITELIST_PACKAGES="" -j8
# 退出码为0即完全成功
echo $?
# 验证核心目标生成
ls -l install/lib/perception_camera_detection/perception_camera_detection
```

## 子窗口详细命令
### win1. roscore
```{code-block} shell
:linenos:
:caption: 启动roscore
# 打开终端
ros-go 
roscore
ls
```
### win2. 播包 rosbag play
```{code-block} shell
:linenos:
:caption: 播包
# 打开终端
ros-go
cd /work/data/Edisk/Edisk_data1/eval_260610after
rosbag play record_2026-06-10-11-16-41.bag --clock -l
ls
```

### win3. 车型配置 local_env_depoly.sh
```{code-block} shell
:linenos:
:caption: 车型配置
start-ros-proj
bash ./install/share/env_common/script/shell/local_env_deploy.sh
``` 
按脚本逻辑，执行完毕后需要指定车号与具体车型;<br>
如果执行的时候出错，如{numref}`图{number}({name})<fig_local-env-deploy-wrong>`所示，
那么有可能是编译的时候出现问题，环境编译见{numref}`代码{number}({name})<code-block_catkin_make install>`
```{figure} ../../_static/screenShot/rosStart/local_env_depolyWrong.png
:width: 85%
:align: center
:name: fig_local-env-deploy-wrong
:alt: 环境部署报错截图
车型部署报错图式
```

### win4. 启动感知环境 local_env_run.sh
```{code-block} shell
:linenos:
:caption: 启动感知环境
:name: code-block_local_env_run.sh
start-ros-proj
bash ./install/share/env_common/script/shell/local_env_run.sh
``` 
执行`local_env_run.sh`需要做一个dos2unix的转换，见`代码{number}({name})<code-block_dos2unix2sh>`

#### 若出现问题需手动下载模型
如果出现跑不了的情况的话，可能是git clone ads_env仓中的模型文件没有下载下来，有以下几个路径的模型需要下载
| **模型路径** | **参考截图** |
| ---- | ---- |
| **`./ads_env/lidar_detection/config/centerpoint_models`** | <a href="../../_static/screenShot/rosStart/onnx_need_screenshot1.png" class="glightbox" data-title="需要下载的onnx模型截图1"><img src="../../_static/screenShot/rosStart/onnx_need_screenshot1.png" alt="onnx模型清单截图1" style="width:280px;"></a> |
| **`./ads_env/camera/camera_detection/config/`** | <a href="../../_static/screenShot/rosStart/onnx_need_screenshot2.png" class="glightbox" data-title="需要下载的onnx模型截图2"><img src="../../_static/screenShot/rosStart/onnx_need_screenshot2.png" alt="onnx模型清单截图2" style="width:280px;"></a> |
| **`./ads_env/camera/image_detection/config/`** | <a href="../../_static/screenShot/rosStart/onnx_need_screenshot3.png" class="glightbox" data-title="需要下载的onnx模型截图3"><img src="../../_static/screenShot/rosStart/onnx_need_screenshot3.png" alt="onnx模型清单截图3" style="width:280px;"></a> |


/mnt/Ddisk/soft/local/TensorRT-8.6.1.6/bin/trtexec \
--onnx=lidar_backbone2d.onnx \
--saveEngine=lidar_backbone2d.engine \
--inputIOFormats=fp16:chw \
--outputIOFormats=fp16:chw \
--fp16 \
--workspace=4096 \
--verbose



### win5. 启动可视化脚本 run_debug_display.sh

不改动原始代码，如果ros不是安装在系统盘而是指定路径，需修改脚本对应路径使其生效;

```{code-block} shell
:linenos:
:caption: local_env_run.sh
start-ros-proj
bash ./install/share/debugging_toolset/scripts/run_debug_display.sh
NODE_NAME="topic_launcher_gui"
PY_SCRIPT="/home/huai/work/huai_work/XCMG_work/MultiSensorPostFusion/catkin_ws/install/share/debugging_toolset/scripts/debug_display.py"
LAUNCH_FILE="debugging_toolset debug_display.launch"
ROS_SETUP="/home/huai/work/huai_work/XCMG_work/MultiSensorPostFusion/catkin_ws/install/setup.bash"
``` 
```{code-block} python
:linenos:
:caption: code-block_debug_display.py
def compress_latest_bag(self, base_name):
    import rospkg
    rp = rospkg.RosPack()
    pkg_path = rp.get_path("debugging_toolset")
    ws_install = os.path.abspath(os.path.join(pkg_path, "../../../../"))
    output_dir = os.path.join(os.path.dirname(ws_install), "data")
    os.makedirs(output_dir, exist_ok=True)
``` 

### winX. 单独看激光雷达点云

```{code-block} shell
:linenos:
:caption: perception_lidar_detection 
start-ros-proj
roslaunch perception_lidar_detection perception_lidar_detection.launch
```



  