cd /home/huai/work/huai_work/XCMG_work/MultiSensorPostFusion/Fusion_Eval/XC_docs/ProjectRoot
rm -rf ./MultiSensorPostFusion/_build
# 输出放到子工程内部
sphinx-build ./MultiSensorPostFusion ./MultiSensorPostFusion/_build/html
sphinx-autobuild ./MultiSensorPostFusion ./MultiSensorPostFusion/_build/html 
