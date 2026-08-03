#!/bin/bash
# 创建文件夹结构
mkdir -p tech-notes/docs/{build,source/{_static,_images,docker/{basics,commands,dockerfile,compose,troubleshoot},linux,k8s,pytorch}}

# 创建空文件
touch tech-notes/docs/source/conf.py
touch tech-notes/docs/source/index.rst
touch tech-notes/docs/source/docker/index.md

echo "目录结构创建完成！"