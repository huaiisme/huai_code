# BevFusion test

自写类

主要做三件事
1. **读磁盘 JSON**：把标注目录下所有 JSON 文件读进内存，存成 Python 列表
2. **建查询索引**：给每张表建 `token → 数组下标` 的字典，实现 O (1) 快速查询
3. **封装常用方法**：`get()` 查详情、`get_sample_data_path()` 取文件路径