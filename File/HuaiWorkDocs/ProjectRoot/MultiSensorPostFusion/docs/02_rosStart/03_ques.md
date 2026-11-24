# 问题
## 过程中（启动后融合感知）可能会碰到的问题
### 自启动命令: ros-go & start-ros-proj
仅使用ros-go与start-ros-proj, 之前折腾了一堆,后来为了简便还是作了修改

```{code-block} shell
:linenos:
:caption: ros-go命令写入
:name: code-block_ros-go update
# 删除原先ros-go相关的内容 然后重新写入
alias ros-go='conda deactivate && source /opt/ros/noetic/setup.bash && echo "✅ ROS Noetic 环境就绪，conda已退出"'
```

```{code-block} shell
:linenos:
:caption: start-ros-proj命令写入
:name: code-block_start-ros-proj update
# 删除bashrc里面的旧的alias
grep -n "start-ros-proj" ~/.bashrc
sed -i '/alias start-ros-proj/d' ~/.bashrc

# 写进~/.bashrc
cat >> ~/.bashrc <<'EOF'

# ===== 感知项目一键环境：cd → ROS Noetic → 推理库 → 项目 install =====
start-ros-proj() {
  # 1. 进入工作空间
  cd /work/huai_work/XCMG_work/MultiSensorPostFusion/catkin_ws || return

  # 2. 退出 conda + 加载 ROS Noetic 基础环境
  conda deactivate
  source /opt/ros/noetic/setup.bash

  # 3. Protobuf 3.7.1
  export PROTOBUF_ROOT=/mnt/Ddisk/soft/local/protobuf-3.7.1-install
  export PATH=${PROTOBUF_ROOT}/bin:$PATH
  export LD_LIBRARY_PATH=${PROTOBUF_ROOT}/lib:$LD_LIBRARY_PATH
  export CPATH=${PROTOBUF_ROOT}/include:$CPATH
  export CMAKE_INCLUDE_PATH=${PROTOBUF_ROOT}/include:$CMAKE_INCLUDE_PATH
  export CMAKE_PREFIX_PATH=${PROTOBUF_ROOT}:$CMAKE_PREFIX_PATH
  export PKG_CONFIG_PATH=${PROTOBUF_ROOT}/lib/pkgconfig:$PKG_CONFIG_PATH

  # 4. CUDA 11.6 + cuDNN 8.9.6
  export CUDA_ROOT=/mnt/Ddisk/soft/local/cuda-11.6
  export PATH=${CUDA_ROOT}/bin:$PATH
  export LD_LIBRARY_PATH=${CUDA_ROOT}/lib64:$LD_LIBRARY_PATH
  export CPATH=${CUDA_ROOT}/include:$CPATH
  export CMAKE_INCLUDE_PATH=${CUDA_ROOT}/include:$CMAKE_INCLUDE_PATH

  # 5. TensorRT 8.6.1.6
  export TRT_ROOT=/mnt/Ddisk/soft/local/TensorRT-8.6.1.6
  export PATH=${TRT_ROOT}/bin:$PATH
  export LD_LIBRARY_PATH=${TRT_ROOT}/lib:$LD_LIBRARY_PATH
  export CPATH=${TRT_ROOT}/include:$CPATH
  export CMAKE_INCLUDE_PATH=${TRT_ROOT}/include:$CMAKE_INCLUDE_PATH
  export CMAKE_PREFIX_PATH=${TRT_ROOT}:$CMAKE_PREFIX_PATH
  export TENSORRT_ROOT=${TRT_ROOT}
  export TENSORRT_DIR=${TRT_ROOT}

  # 6. OpenCV 4.5.4 with CUDA
  export OPENCV_ROOT=/mnt/Ddisk/soft/local/opencv-4.5.4-install
  export PATH=${OPENCV_ROOT}/bin:$PATH
  export LD_LIBRARY_PATH=${OPENCV_ROOT}/lib64:$LD_LIBRARY_PATH
  export CPATH=${OPENCV_ROOT}/include:$CPATH
  export CMAKE_INCLUDE_PATH=${OPENCV_ROOT}/include:$CMAKE_INCLUDE_PATH
  export CMAKE_PREFIX_PATH=${OPENCV_ROOT}:$CMAKE_PREFIX_PATH
  export PKG_CONFIG_PATH=${OPENCV_ROOT}/lib64/pkgconfig:$PKG_CONFIG_PATH

  # 7. 清命令缓存 + 加载当前工作空间 ROS 包
  hash -r
  source install/setup.bash

  echo "✅ 感知项目全套环境加载完成 | Protobuf3.7.1 + CUDA11.6 + TRT8.6.1 + OpenCV4.5.4"
}
EOF

# 重载并验证
source ~/.bashrc
type start-ros-proj

# 跑一次 + 校验环境
start-ros-proj
pwd
rospack find env_common
nvcc -V
protoc --version
pkg-config --modversion opencv4

```

### dos2unix
然后由于脚本local_env_run.sh是windows上或者是wsl的，还需要做一个dos2unix的转换
```{code-block} shell
:linenos:
:caption: dos2unix转换.sh
:name: code-block_dos2unix2sh
使用dos2unix 修改
# 先安装工具
sudo apt install dos2unix -y

# 进入脚本目录，批量转换所有 .sh 文件
cd /work/huai_work/XCMG_work/MultiSensorPostFusion/catkin_ws/install/share/env_common/script/shell/
dos2unix *.sh
```