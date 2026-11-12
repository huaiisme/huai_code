# 后融合感知环境部署(Ubuntu 20.04 ROS1)
根据峰奇跟娇姐给到的{download}`感知环境部署步骤.txt <../../files/感知环境部署步骤.txt>`安装，包含部分根据自己工作站相关调整部分，如果步骤存在问题的话，需要自行在查一下，可将报错部分给到AI去作相应调整。

## Ubuntu 20.04 ROS1 环境
### 安装 ROS Noetic
ubuntu 20.04 ros1 对应的是ros noetic
<!-- 引用写法：{numref}`%s <catkin-init>` -->
```{code-block} shell
:linenos:
:caption: 安装 ROS Noetic
:name: install_ros-noetic-full
sudo apt install ros-noetic-desktop-full
```

## 安装定位 gps-common 模块 & msg软件包 & Rviz插件
```{code-block} shell
:linenos:
:caption: 安装定位 gps-common 模块 & msg软件包 及 Rviz插件
:name: install ros-noetic-gps-common & ros-noetic-jsk
sudo apt install  -y \
                  ros-noetic-swri-nodelet \
                  ros-noetic-swri-string-util \
                  ros-noetic-swri-math-util \
                  ros-noetic-swri-serial-util \
                  ros-noetic-gps-common \
                  ros-noetic-swri-roscpp         
sudo apt-get install ros-noetic-jsk-recognition-msgs
sudo apt-get install ros-noetic-jsk-rviz-plugins
```

## 安装protobuf & cuda & cudnn & tensorrt
根据所给文件，将protobuf & cuda & cudnn & tensorrt 安装在一个/mnt/Ddisk/soft/local/文件下

【深度学习GPU驱动环境配置】ubuntu20.04中cuda11.6、cuDNN8.9.6、anaconda的安装 
```{code-block} shell
:linenos:
:caption: 安装结构图
/mnt/Ddisk/soft/local/
├── protobuf-3.7.1-install/
├── cuda-11.6/                # CUDA11.6安装目录
├── load-proto37.sh
└── load-cuda116.sh           # CUDA环境切换脚本
```



### 安装protobuf 

```{code-block} shell
:linenos:
:caption: 安装protobuf-all-3.7.1
:name: install_proto37
cd /mnt/Ddisk/soft/local
哪怕终端里 protoc 是别的版本，CMake 想强制用这套 3.7.1，编译时加参数：
cmake .. -DCMAKE_PREFIX_PATH=/mnt/Ddisk/soft/local/protobuf-3.7.1-install
```

<!-- :::{admonition} 问
:class: tip qa-compact
**Q：** source .sh 跟 bash xxx.sh 的区别是什么

**A：** `bash xxx.sh`：新开独立子 shell 运行脚本，脚本内环境变量执行结束自动销毁，不影响当前终端; `source xxx.sh`（等价于 `. xxx.sh`）：在当前 shell 进程执行，`export` 的环境变量保留在当前终端。
::: -->

:::{Tip}
:class: tip qa-compact
**Q：** source .sh 跟 bash xxx.sh 的区别是什么

**A：** `bash xxx.sh`：新开独立子 shell 运行脚本，脚本内环境变量执行结束自动销毁，不影响当前终端; `source xxx.sh`（等价于 `. xxx.sh`）：在当前 shell 进程执行，`export` 的环境变量保留在当前终端。
:::

### 适配ROS Noetic安装CUDA 11.6

```{code-block} shell
:linenos:
:caption: 下载 & 安装CUDA 11.6 runfile 
:name: install_CUDA116

mkdir -p /mnt/Ddisk/soft/Downloads
cd /mnt/Ddisk/soft/Downloads
wget https://developer.download.nvidia.com/compute/cuda/11.6.0/local_installers/cuda_11.6.0_510.39.01_linux.run

sudo sh cuda_11.6.0_510.39.01_linux.run \
--silent \
--toolkit \
--toolkitpath=/mnt/Ddisk/soft/local/cuda-11.6 \
--no-opengl-libs

sudo chown -R huai:huai /mnt/Ddisk/soft/local/cuda-11.6

# 创建 CUDA 按需加载脚本
cat > /mnt/Ddisk/soft/local/load-cuda116.sh <<'EOF'
#!/bin/bash
export CUDA_HOME=/mnt/Ddisk/soft/local/cuda-11.6
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
echo "===== 已切换至 CUDA 11.6 ====="
nvcc -V
EOF
chmod +x /mnt/Ddisk/soft/local/load-cuda116.sh

# 测试CUDA
source /mnt/Ddisk/soft/local/load-cuda116.sh

```


### 安装cudnn

cudnn8.9.6 需要去nvidia官网去下
下载地址：[https://developer.nvidia.com/rdp/cudnn-archive](https://developer.nvidia.com/rdp/cudnn-archive)
选择：`cudnn-linux-x86_64-8.9.6.50_cuda11-archive.tar.xz`


```{code-block} shell
:linenos:
:caption: 下载 & 安装cudnn 8.9.6

cudnn-linux-x86_64-8.9.6.50_cuda11-archive.tar.xz

cd /mnt/Ddisk/soft/Downloads
tar -xvf cudnn-linux-x86_64-8.9.6.50_cuda11-archive.tar.xz

CUDA_PATH=/mnt/Ddisk/soft/local/cuda-11.6

cp include/cudnn*.h $CUDA_PATH/include/
cp -P lib/libcudnn* $CUDA_PATH/lib64/
chmod a+r $CUDA_PATH/include/cudnn*.h $CUDA_PATH/lib64/libcudnn*

```


### TensorRT



根据所给的文档，安装感知环境配置
TensorRT 同样走**tar 包隔离安装**（不和系统、conda 冲突，和你 protobuf、cuda 一套思路）
https://developer.nvidia.com/downloads/compute/machine-learning/tensorrt/secure/8.6.1/tars/TensorRT-8.6.1.6.Linux.x86_64-gnu.cuda-11.8.tar.gz

```{code-block} shell
:linenos:
:caption: 下载 & 安装tensorRT
conda activate bevfusion-dev
pip install ./tensorrt-8.6.1-cp38-none-linux_x86_64.whl

```


### opencv 4.5.4 & opencv contrib 4.5.4
按照AI提示一步步安装

### 修改一键环境
load-ros-env 一键环境
```{code-block} shell
:linenos:
:caption: 一键环境
alias load-ros-env='source /mnt/Ddisk/soft/local/load-all.sh; hash -r; echo "hash cache cleared!"'
load-bev-env
opencv_version
which opencv_version
nvcc -V
protoc --version
```

## 环境编译
这边编译过了，删掉重新再弄一遍，主要是为了不动cmakelist，在别的地方作一些改动
环境编译多多少少会碰到一些问题，同样也是将报错记录给到AI去作相应调整，主要先根据ads_env中的readme.md根据报错情况作相应修改 比较容易出现的是找不到tensorRT, 或者是opencv环境，需要将你所下载的位置对ads_env中的cmakelist.txt做一些微调


```{code-block} shell
:linenos:
:caption: 创建编译环境路径目录 & git clone ads_env
:name: ros1 catkin_ws/src git clone ads_env

# 可进到自己的工作空间 + 拉取纯净代码
cd /home/huai/work/huai_work/XCMG_work/MultiSensorPostFusion 
mkdir -p catkin_ws/src
git clone ads_env
cd ads_env
# 切到release版本代码
git checkout release
mv ads_env ./catkin_ws/src   
```

```{code-block} shell
:linenos:
:caption: catkin_make创建环境
:name: ros1 catkin_make catkin_ws/src 
cd /work/huai_work/XCMG_work/MultiSensorPostFusion/catkin_ws
# 我自己的conda deactivate 切到ros环境的alias命令
# alias ros-go='conda deactivate && source /opt/ros/noetic/setup.bash && [ -f ~/ros_ws/devel/setup.bash && echo "✅ ROS Noetic 环境就绪，conda已退出"'

ros-go
# 同样的把1.X里面的安装的环境一键启动alias命令


```

```{code-block} shell
:linenos:
:caption: 完善load-all.sh
:name: update load-all.sh



#!/bin/bash
# load-all.sh : 一次性加载整套环境 protobuf3.7.1 + cuda11.6 + cudnn8.9.6 + TensorRT8.6.1 + OpenCV4.5.4

# 1. Protobuf 3.7.1
export PROTOBUF_ROOT=/mnt/Ddisk/soft/local/protobuf-3.7.1-install
export PATH=${PROTOBUF_ROOT}/bin:$PATH
export LD_LIBRARY_PATH=${PROTOBUF_ROOT}/lib:$LD_LIBRARY_PATH
# ===== 新增：头文件 + CMake 找包路径 =====
export CPATH=${PROTOBUF_ROOT}/include:$CPATH
export CMAKE_INCLUDE_PATH=${PROTOBUF_ROOT}/include:$CMAKE_INCLUDE_PATH
export CMAKE_PREFIX_PATH=${PROTOBUF_ROOT}:$CMAKE_PREFIX_PATH
export PKG_CONFIG_PATH=${PROTOBUF_ROOT}/lib/pkgconfig:$PKG_CONFIG_PATH

# 2. CUDA 11.6 + cuDNN8.9.6
export CUDA_ROOT=/mnt/Ddisk/soft/local/cuda-11.6
export PATH=${CUDA_ROOT}/bin:$PATH
export LD_LIBRARY_PATH=${CUDA_ROOT}/lib64:$LD_LIBRARY_PATH
# ===== 新增：头文件路径 =====
export CPATH=${CUDA_ROOT}/include:$CPATH
export CMAKE_INCLUDE_PATH=${CUDA_ROOT}/include:$CMAKE_INCLUDE_PATH

# 3. TensorRT 8.6.1.6
export TRT_ROOT=/mnt/Ddisk/soft/local/TensorRT-8.6.1.6
export PATH=${TRT_ROOT}/bin:$PATH
export LD_LIBRARY_PATH=${TRT_ROOT}/lib:$LD_LIBRARY_PATH
# ===== 新增：头文件 + CMake 找包路径 =====
export CPATH=${TRT_ROOT}/include:$CPATH
export CMAKE_INCLUDE_PATH=${TRT_ROOT}/include:$CMAKE_INCLUDE_PATH
export CMAKE_PREFIX_PATH=${TRT_ROOT}:$CMAKE_PREFIX_PATH
export TENSORRT_ROOT=${TRT_ROOT}
export TENSORRT_DIR=${TRT_ROOT}

# 4. OpenCV 4.5.4 with CUDA
export OPENCV_ROOT=/mnt/Ddisk/soft/local/opencv-4.5.4-install
export PATH=${OPENCV_ROOT}/bin:$PATH
export LD_LIBRARY_PATH=${OPENCV_ROOT}/lib64:$LD_LIBRARY_PATH
# ===== 新增：头文件 + CMake 找包路径 =====
export CPATH=${OPENCV_ROOT}/include:$CPATH
export CMAKE_INCLUDE_PATH=${OPENCV_ROOT}/include:$CMAKE_INCLUDE_PATH
export CMAKE_PREFIX_PATH=${OPENCV_ROOT}:$CMAKE_PREFIX_PATH
export PKG_CONFIG_PATH=${OPENCV_ROOT}/lib64/pkgconfig:$PKG_CONFIG_PATH

echo "===== Load env done ====="
echo "Protobuf root: ${PROTOBUF_ROOT}"
echo "CUDA root: ${CUDA_ROOT}"
echo "TensorRT root: ${TRT_ROOT}"
echo "OpenCV root: ${OPENCV_ROOT}"
echo "========================="


```





```{code-block} shell
:linenos:
:caption: catkin_make环境编译
:name: catkin_make install
cd /work/huai_work/XCMG_work/MultiSensorPostFusion/catkin_ws

# 1. 清缓存（必须，旧配置会残留）
rm -rf build devel install

# 2. 按顺序加载环境
ros-go
load-ros-env

# 3. 直接编译，只需要基础参数
catkin_make install -DCMAKE_BUILD_TYPE=Release
# 退出码为0即完全成功
echo $?
# 验证核心目标生成
ls -l install/lib/perception_camera_detection/perception_camera_detection
```


```{code-block} shell
:linenos:
:caption: 日常运行程序

# 1. 进入工作空间根目录
cd /work/huai_work/XCMG_work/MultiSensorPostFusion/catkin_ws
# 2. 加载 ROS Noetic 基础环境
ros-go
# 3. 加载算法依赖（CUDA/TensorRT/Protobuf/OpenCV，脚本已内置所有路径）
load-ros-env
# 4. 加载当前工作空间的 ROS 程序
source install/setup.bash

bash ./install/share/env_common/script/shell/local_env_run.sh
```

### dos2unix
然后由于脚本local_env_run.sh是windows上或者是wsl的，还需要做一个dos2unix的转换
```{code-block} shell
:linenos:
:caption: dos2unix

使用dos2unix 修改
# 先安装工具
sudo apt install dos2unix -y

# 进入脚本目录，批量转换所有 .sh 文件
cd /work/huai_work/XCMG_work/MultiSensorPostFusion/catkin_ws/install/share/env_common/script/shell/
dos2unix *.sh
```