# BevFusion 环境配置

```{code-block} shell
:linenos:
:caption: 空白

```

## conda安装
```{code-block} shell
:linenos:
:caption: Ubuntu 安装Miniconda到 /mnt/Ddisk/soft（数据盘）
# 清华镜像下载安装脚本
wget https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
# 静默安装，指定安装位置
bash miniconda.sh -b -p /mnt/Ddisk/soft/miniconda3
# 激活conda
source /mnt/Ddisk/soft/miniconda3/bin/activate
conda init bash
# 删除安装包
rm miniconda.sh
```

```{code-block} shell
:linenos:
:caption: conda安装
# 新增了TOS条款
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

conda create -n bevfusion-dev python=3.8 -y
conda activate bevfusion-dev

# 如果碰到问题
CONDA_NO_PLUGINS=true conda create -n bevfusion-dev python=3.8 -y --solver classic
```

## huai_PC linux 安装CPU版Pytorch
```{code-block} shell
:linenos:
:caption: 安装CPU版Pytorch
在激活的bevfusion-dev环境中执行下列命令
python -m pip install torch==2.0.1 torchvision==0.15.2 \
  --index-url https://download.pytorch.org/whl/cpu \
  --default-timeout=100 \
  --retries 5

```

补充说明：后续安装 numpy、nuscenes-devkit 这类**普通 Python 包**时，用 `-i https://pypi.tuna.tsinghua.edu.cn/simple` 是正常可用的；只有 PyTorch 这种带 `+cpu/+cu118` 定制后缀的包不在普通 pypi 源里，需要单独处理。


## 先配置 pip 全局国内源（根治下载超时）

先把 pip 全局换成清华源，后续装所有包都能提速，避免再出现 `ReadTimeout` 报错。


```{code-block} shell
:linenos:
:caption: 安装CPU版Pytorch
# 配置全局清华源
python -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
# 配置信任主机
python -m pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 验证配置是否生效
python -m pip config list

```

## 安装 OpenMMLab 全家桶
mmcv 是 3D 检测框架的基础依赖，**必须安装 CPU 专属版本**，不能直接默认安装，否则会自动找 GPU 依赖报错。
### 2.1 安装 OpenMIM 包管理工具
python -m pip install -U openmim


### 2.2 依次安装核心库（严格 CPU 版）
```{code-block} shell
:linenos:
:caption: 2.2 依次安装核心库（严格 CPU 版）
# 1. 基础引擎
mim install mmengine==0.8.4
# 2. 安装 CPU 版 mmcv（最关键，指定 CPU 源）
mim install "mmcv==2.0.1" -f https://download.openmmlab.com/mmcv/dist/cpu/torch2.0/index.html
# 3. 检测基础库
mim install mmdet==3.1.0
# 4. 3D 检测库
mim install mmdet3d==1.1.0
```

### 2.3 验证
```{code-block} shell
:linenos:
:caption: 2.3 验证导入
python -c "import mmcv, mmdet, mmdet3d; print('OpenMMLab 全家桶导入成功')"

# 如果碰到一些问题 需要向下兼容 在随时改
python -m pip uninstall mmdet -y
mim install mmdet==3.0.0

```
📌 重要说明：**spconv 暂时不用装**。CPU 环境下稀疏卷积效率极低且兼容问题多，前期 LiDAR 分支的逻辑验证，用 PyTorch 原生 `nn.Conv3d`（稠密卷积）就能跑通代码框架，等上云训练时再替换成 spconv 即可，完全不影响你从零实现的代码设计。


OpenMMLab 全家桶导入成功


