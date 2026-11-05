import json
from pathlib import Path


class MyNuScenes:
    """
    自研极简版 nuScenes 数据读取类
    完全兼容官方 API：sample["data"]、sample["anns"] 直接可用
    """

    def __init__(self, version: str, dataroot: str, verbose: bool = True):
        self.dataroot = Path(dataroot)
        self.version = version
        self.verbose = verbose

        # 步骤1：加载所有JSON标注表
        self._load_all_json_tables()

        # 步骤2：构建 token 反向索引
        self._build_token_index()

        # 步骤3：给sample聚合 data 和 anns 字段
        self._build_sample_aggregation()

        if self.verbose:
            print("======")
            print("Reverse indexing done.")
            print("======")

    # ===================== 步骤1：加载所有JSON表 =====================
    def _load_all_json_tables(self):
        table_dir = self.dataroot / self.version
        table_names = [
            "category", "scene", "sample", "sample_data",
            "sample_annotation", "calibrated_sensor", "ego_pose",
            "attribute", "visibility", "instance", "log", "map"
        ]

        for table_name in table_names:
            json_path = table_dir / f"{table_name}.json"
            if not json_path.exists():
                continue
            with open(json_path, "r", encoding="utf-8") as f:
                table_data = json.load(f)
            setattr(self, table_name, table_data)
            if self.verbose:
                print(f"{len(table_data)} {table_name}")

        if self.verbose:
            print("Done loading all tables.")

    # ===================== 步骤2：构建token索引 =====================
    def _build_token_index(self):
        self._token2idx = {}
        index_tables = [
            "sample", "sample_data", "sample_annotation",
            "calibrated_sensor", "ego_pose", "scene",
            "category", "instance", "log", "map"
        ]

        for table_name in index_tables:
            table_data = getattr(self, table_name, [])
            idx_map = {}
            for idx, item in enumerate(table_data):
                idx_map[item["token"]] = idx
            self._token2idx[table_name] = idx_map

    # ===================== 步骤3：聚合sample的data和anns字段 =====================
    def _build_sample_aggregation(self):
        """
        给每个 sample 补充两个便利字段：
        - data: {传感器名称: sample_data_token}
        - anns: [annotation_token1, annotation_token2, ...]  本帧所有标注框的token
        """
        # 先给所有 sample 初始化空字段
        for s in self.sample:
            s["data"] = {}
            s["anns"] = []

        # --- 聚合 data 字段 ---
        for sd in self.sample_data:
            sample_token = sd["sample_token"]
            # 从文件路径提取传感器名称
            sensor_name = Path(sd["filename"]).parent.name
            # 索引快速定位sample
            sample_idx = self._token2idx["sample"][sample_token]
            self.sample[sample_idx]["data"][sensor_name] = sd["token"]

        # --- 聚合 anns 字段（新增修复）---
        for ann in self.sample_annotation:
            sample_token = ann["sample_token"]
            ann_token = ann["token"]
            # 索引快速定位sample
            sample_idx = self._token2idx["sample"][sample_token]
            self.sample[sample_idx]["anns"].append(ann_token)

        if self.verbose:
            print(f"Sample 聚合完成，共 {len(self.sample)} 帧")

    # ===================== 核心方法：按token查询 =====================
    def get(self, table_name: str, token: str) -> dict:
        if table_name not in self._token2idx:
            raise ValueError(f"不存在的数据表: {table_name}")
        idx = self._token2idx[table_name][token]
        return getattr(self, table_name)[idx]

    # ===================== 核心方法：获取文件路径 =====================
    def get_sample_data_path(self, sample_data_token: str) -> str:
        sd_record = self.get("sample_data", sample_data_token)
        full_path = self.dataroot / sd_record["filename"]
        return str(full_path)
