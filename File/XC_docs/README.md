# Project for sphinx


cd ./ProjectRoot

make BevFusion
cd BevFusion
sphinx-autobuild . _build/html

rm -rf .MultiSensorPostFusion/_build
make MultiSensorPostFusion
sphinx-autobuild ./MultiSensorPostFusion _build/html



make aggregate
python3 merge_search_index.py
cd aggregate/_build/html
python3 -m http.server 8003 --bind 0.0.0.0



