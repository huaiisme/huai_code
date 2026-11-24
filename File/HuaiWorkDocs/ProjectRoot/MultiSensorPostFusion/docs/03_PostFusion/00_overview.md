# 后融合Overview

根据前面的ros的启动，现在可以根据运行的程序去对程序做一个细究，入口就是从{numref}`代码{number}({name})<code-block_local_env_run.sh>`
不过现在还是从激光雷达的角度去看问题 还没有从图像的层面去看

脚本的入口为`./install/share/env_common/script/shell/local_env_run.sh`
那么需要在原始的src去搜索原始的local_env_run.sh

```{code-block} shell
:linenos:
:caption: 执行搜索命令
cd /home/huai/work/huai_work/XCMG_work/MultiSensorPostFusion/catkin_ws
find ./src -name "local_env_run.sh"
```

```{code-block} shell
:caption: 命令输出结果
./src/ads_env/env_common/script/shell/local_env_run.sh
```


