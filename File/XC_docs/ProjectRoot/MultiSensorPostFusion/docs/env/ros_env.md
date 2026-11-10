# Ubuntu 20.04 ROS1 环境配置

## 安装 ROS Noetic


引用写法：{numref}`%s <catkin-init>`
```{code-block} shell
:linenos:
:caption: 安装 ROS Noetic
:name: install_ros-noetic-full

sudo apt install ros-noetic-desktop-full
```
ubuntu 20.04 ros1 对应的是ros noetic，有关内容一些ros安装的步骤如果出现一些问题的话，可以参照各个AI对话把出现ERROR的LOG全部拷贝过去 基本上都能解决

## 安装定位 gps-common 模块
```{code-block} shell
:linenos:
:caption: 安装定位 gps-common 模块
:name: install_ros-noetic-gps-common

sudo apt install  -y \
                  ros-noetic-swri-nodelet \
                  ros-noetic-swri-string-util \
                  ros-noetic-swri-math-util \
                  ros-noetic-swri-serial-util \
                  ros-noetic-gps-common \
                  ros-noetic-swri-roscpp
                  
```

## msg软件包及Rviz插件
```{code-block} shell
:linenos:
:caption: 安装 msg软件包 及 Rviz插件
:name: install_ros-noetic-jsk
sudo apt-get install ros-noetic-jsk-recognition-msgs
sudo apt-get install ros-noetic-jsk-rviz-plugins
```

## msg软件包及Rviz插件
```{code-block} shell
:linenos:
:caption: 安装 msg软件包 及 Rviz插件
:name: install_ros-noetic-jsk
sudo apt-get install ros-noetic-jsk-recognition-msgs
sudo apt-get install ros-noetic-jsk-rviz-plugins
```

## 安装protobuf
安装在一个临时文件夹下
```{code-block} shell
:linenos:
:caption: 安装protobuf-all-3.7.1
:name: install_proto37
cd /mnt/Ddisk/soft/local
哪怕终端里 protoc 是别的版本，CMake 想强制用这套 3.7.1，编译时加参数：
cmake .. -DCMAKE_PREFIX_PATH=/mnt/Ddisk/soft/local/protobuf-3.7.1-install
```
Q： source .sh 跟bash .sh的区别是什么
A： - `bash xxx.sh`：**新开一个独立子 shell 运行脚本**，脚本里改的环境变量，跑完自动消失，不影响你当前终端。
    - `source xxx.sh`（等价于 `. xxx.sh`）：**直接在你当前这个 shell 进程里面执行脚本**，里面 `export` 的环境变量会留在当前终端，持续生效。

## 安装配置cuda & cudnn & tensorrt

【深度学习GPU驱动环境配置】ubuntu20.04中cuda11.6、cuDNN8.9.6、anaconda的安装 

/mnt/Ddisk/soft/local/
├── protobuf-3.7.1-install/
├── cuda-11.6/                # CUDA11.6安装目录
├── load-proto37.sh
└── load-cuda116.sh           # CUDA环境切换脚本

### 安装CUDA 
```{code-block} shell
:linenos:
:caption: 下载 & 安装CUDA 11.6 runfile 

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
按照AI工具一步步安装


### 修改一键环境

```{code-block} shell
:linenos:
:caption: 一键环境
alias load-bev-env='source /mnt/Ddisk/soft/local/load-all.sh; hash -r; echo "hash cache cleared!"'
load-bev-env
opencv_version
which opencv_version
nvcc -V
protoc --version

```


