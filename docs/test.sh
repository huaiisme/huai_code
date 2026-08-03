#!/bin/bash

# 创建目录结构
mkdir -p basics commands dockerfile compose troubleshoot

# 生成各个md文件并写入一级标题
echo "# intro" > basics/intro.md
echo "# install" > basics/install.md
echo "# basic" > commands/basic.md
echo "# grammar" > dockerfile/grammar.md
echo "# basic" > compose/basic.md
echo "# common_errors" > troubleshoot/common_errors.md

# 生成顶层index.rst
cat > index.rst << 'EOF'
# # Docker 学习笔记

# ## 专栏介绍
# 记录 Docker 容器基础、常用命令、Dockerfile、Compose、镜像管理、故障排查。

# ```{toctree}
# :maxdepth: 3
# basics/intro
# basics/install
# commands/basic
# dockerfile/grammar
# compose/basic
# troubleshoot/common_errors