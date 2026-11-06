# Ubuntu 20.04 ROS1 环境配置

## 安装 ROS Noetic

```{code-block} shell
:linenos:
:caption: 安装 ROS Noetic
:name: ros-noetic-install

sudo apt install ros-noetic-desktop-full
```

引用写法：{numref}`%s <ros-noetic-install>`

## 初始化工作空间

```{code-block} shell
:linenos:
:caption: 初始化 catkin 工作空间
:name: catkin-init

mkdir -p ~/catkin_ws/src
cd ~/catkin_ws
catkin_make
```

引用写法：{numref}`%s <catkin-init>`
