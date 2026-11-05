import json
import os
from pathlib import Path


class MyNuScenes:
    """
    自研极简版 nuScenes 数据读取类
    功能：加载JSON标注、建token索引、快速查询、获取文件路径
    可直接替换官方 NuScenes 类，API 完全兼容
    """
    def __init__(self, version: str, dataroot: str, verbose: bool = True):
        """
        初始化入口，对应官方NuScenes()
        :param version: 数据集版本，比如 'v1.0-mini'
        :param dataroot: 数据集根目录
        :param verbose: 是否打印加载日至
        """
        self.dataroot = Path(dataroot) #数据集根目录
        print(self.dataroot)
        self.version = version # 版本号
        self.verbose = verbose

        # # 步骤1: 加载所有json标注表
        self._load_all_json_tables()

        # # 步骤2: 构建token反向索引
        self._build_token_index()

        if self.verbose:
            print("======")
            print("Reverse indexing done.")
            print("======")

# ===================== 核心步骤1：加载所有JSON表 =====================
    def _load_all_json_tables(self):
        """读取版本目录下所有JSON文件，存为对象属性"""
        # 标注文件所在目录：dataroot/v1.0-mini/
        table_dir = self.dataroot / self.version
        print(table_dir)
        # nuScenes 所有标注表的文件名（去掉.json后缀）
        table_names = [
            "category",
            "scene",
            "sample",
            "sample_data",
            "sample_annotation",
            "calibrated_sensor",
            "ego_pose",
            "attribute",
            "visibility",
            "instance",
            "log",
            "map"
        ]

        for table_name in table_names:
            json_path = table_dir / f"{table_name}.json"     
            print(json_path)

            # 文件不存在就跳过（mini版可能缺个别次要表）
            if not json_path.exists():
                continue

            # 读取JSON文件，内容是一个列表
            with open(json_path, "r", encoding="utf-8") as f:
                table_data = json.load(f)

            # 把列表设置为对象的属性，比如 self.sample = [...] 把table_name里面的key 变成了 self.key = table_data
            setattr(self, table_name, table_data)
            
            if self.verbose:
                print(f"{len(table_data)} {table_name}")

        if self.verbose:
            print("Done loading all tables.")

# ===================== 核心步骤2：构建token索引 =====================
    def _build_token_index(self):
        """
        为每张表建立 token -> 数组下标 的映射字典
        后续查询token时，不用遍历列表，O(1) 就能找到位置
        """
        self._token2idx = {} # 总索引字典: {表名}
        index_tables = [
            "category",
            "scene",
            "sample",
            "sample_data",
            "sample_annotation",
            "calibrated_sensor",
            "ego_pose",
            "instance",
            "log",
            "map"
        ]

        for table_name in index_tables:
            # 拿到这张表的所有数据
            table_data = getattr(self, table_name, [])
            idx_map = {}

            # 遍历每条数据，记录 token 对应的数组下标
            for idx, item in enumerate(table_data):
                token = item["token"]
                idx_map[token] = idx

            self._token2idx[table_name] = idx_map



print('1')