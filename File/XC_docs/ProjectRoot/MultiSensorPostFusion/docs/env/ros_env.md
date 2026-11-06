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




根据所给的文档，安装感知环境配置


















