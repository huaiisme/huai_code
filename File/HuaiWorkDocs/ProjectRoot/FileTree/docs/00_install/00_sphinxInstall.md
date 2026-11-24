# sphinx-build安装命令 & 启动
## 前置项安装 pip3
```{code-block} shell
:linenos:
:caption: sphinx安装
:name: code-block install_pip3
# 先装pip3（如果没有）
sudo apt install python3-pip -y
```

##  安装sphinx与相应配置项

```{code-block} shell
:linenos:
:caption: sphinx安装
:name: code-block install_sphinx

# 配置清华源
mkdir -p ~/.config/pip
nano ~/.config/pip/pip.conf
# 并写入下述内容
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn

# 安装 sphinx + sphinx-autobuild
pip3 install sphinx sphinx-autobuild myst-parser
pip3 install sphinx-multitoc-numbering sphinx_copybutton
pip3 install sphinx-rtd-theme
pip3 install linkify-it-py

#pip 不带 sudo 安装，**sphinx-build、sphinx-autobuild 被放到 `~/.local/bin/`**
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## 启动sphinx
```{code-block} shell
:linenos:
:caption: sphinx启动
:name: code-block start_sphinx
# 编辑脚本内容，启动sphinx, build 是生成静态 auto-build是生成一个在线http
cd /home/huai/huai_work/Personal_work/huai_code/File/Huai_docs/ProjectRoot
rm -rf ./FileTree/_build
# 输出放到子工程内部
sphinx-build ./FileTree ./FileTree/_build/html
sphinx-autobuild ./FileTree ./FileTree/_build/html 
```





