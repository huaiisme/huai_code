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

# 改用 Python 离线库 `cmudict`
pip install cmudict
<!-- 基于 CMU 美式发音词典，本地内置完整词库，生成全程无需联网），自动转换为标准 IPA 音标 -->