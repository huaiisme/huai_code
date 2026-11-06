# huai_code
redo my proj and set the sphinx for main branch

sphinx-autobuild source build/html

sudo apt install python3-sphinx-autobuild

python3 -m pip install sphinx sphinx-autobuild myst_parser sphinx-rtd-theme
python3 -m pip install sphinx-copybutton sphinx-design linkify-it-py
python3 -m pip install linkify-it-py

# 改用 Python 离线库 `cmudict`
pip install cmudict
<!-- 基于 CMU 美式发音词典，本地内置完整词库，生成全程无需联网），自动转换为标准 IPA 音标 -->