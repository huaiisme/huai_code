# ros1 安装
## 适配ubuntu20.04的ros noetic安装
### ROS Noetic安装
在Ubuntu20.04版本下安装ROS1对应位Ros Noetic
```{code-block} shell
:linenos:
:caption: 安装 ROS Noetic
:name: code-block install_ros-noetic-full

# 1. 先安装依赖工具
sudo apt update
sudo apt install curl software-properties-common
**[raw.githubusercontent.com](https://raw.githubusercontent.com) 在国内访问不通**，换密钥服务器方案（不用 curl 拉 github），直接用密钥服务器导入，清华 ROS 源不变。
# 1. 添加ROS清华源
echo "deb http://mirrors.tuna.tsinghua.edu.cn/ros/ubuntu focal main" | sudo tee /etc/apt/sources.list.d/ros-latest.list
# 2. 从ubuntu密钥服务器导入ROS密钥（重点！避开raw.githubusercontent）
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654
sudo apt update
# 再安装
sudo apt install ros-noetic-desktop-full

# 1. 把 noetic 环境写入 bashrc
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
# 生效
source ~/.bashrc
```
###  rosdep

```{code-block} shell
:linenos:
:caption: ROS Noetic 环境配置 + 编译依赖安装
:name: code-block install rosdep
# 安装 rosdep、编译工具链
sudo apt install python3-rosdep python3-rosinstall python3-rosinstall-generator python3-wstool build-essential

```

## 感知环境部署
### 安装定位 gps-common 模块 & msg软件包 & Rviz插件
```{code-block} shell
:linenos:
:caption: 安装定位 gps-common 模块 & msg软件包 及 Rviz插件
:name: code-block install ros-noetic-gps-common & ros-noetic-jsk
PACKAGES=(
    ros-noetic-swri-nodelet
    ros-noetic-swri-string-util
    ros-noetic-swri-math-util
    ros-noetic-swri-serial-util
    ros-noetic-gps-common
    ros-noetic-swri-roscpp
)
sudo apt install -y "${PACKAGES[@]}"
sudo apt-get install ros-noetic-jsk-recognition-msgs
sudo apt-get install ros-noetic-jsk-rviz-plugins
```





