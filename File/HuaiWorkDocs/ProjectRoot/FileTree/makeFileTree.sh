cd /home/huai/huai_work/Personal_work/huai_code/File/HuaiWorkDocs/ProjectRoot/FileTree
rm -rf ./_build
# 输出放到子工程内部
sphinx-build ./ ./_build/html
sphinx-autobuild ./ ./_build/html 
