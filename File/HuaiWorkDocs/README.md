# Project for sphinx


cd ./ProjectRoot


make aggregate
python3 merge_search_index.py
cd aggregate/_build/html
python3 -m http.server 8003 --bind 0.0.0.0

如果sphinx 有点问题 可以强制刷新或者使用无痕模式
火狐 ctrl+shift+p 
强制刷新ctrl+F5

