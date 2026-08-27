# huai_code
redo my proj and set the sphinx for main branch

pip install sphinx sphinx-rtd-theme
sudo apt install python3-sphinx
sudo apt install python3-sphinx-autobuild

## 验证安装
sphinx-build --version
## 快速启动
sphinx-quickstart docs

## 建立
sphinx-autobuild docs/source docs/build/html
sphinx-autobuild source build/html