AGG_OUT := aggregate/_build/html
PROJECTS := BevFusion FileTree MultiSensorPostFusion

.PHONY: all stage1 stage2 build aggregate clean help
# 重点：把三个工程加到 PHONY，告诉 make：这三个不是文件/文件夹名，每次都要执行
.PHONY: BevFusion FileTree MultiSensorPostFusion

help:
	@echo "===== 命令列表 ====="
	@echo "  make BevFusion                 单独构建 BevFusion"
	@echo "  make FileTree                  单独构建 FileTree"
	@echo "  make MultiSensorPostFusion     单独构建 MultiSensorPostFusion"
	@echo "  make all                       全量构建 + 聚合站点 + 合并搜索索引"
	@echo "  make clean                     清空所有构建产物"

BevFusion:
	cd BevFusion && sphinx-build . _build/html

FileTree:
	cd FileTree && sphinx-build . _build/html

MultiSensorPostFusion:
	cd MultiSensorPostFusion && sphinx-build . _build/html

stage1:
	@for p in $(PROJECTS); do \
		echo ">> 第一轮（生成 inventory）：$$p"; \
		(cd $$p && sphinx-build -q . _build/html) || true; \
	done

stage2:
	@for p in $(PROJECTS); do \
		echo ">> 第二轮（完整构建）：$$p"; \
		(cd $$p && sphinx-build . _build/html); \
	done

build: stage1 stage2

aggregate:
	rm -rf $(AGG_OUT)
	sphinx-build aggregate $(AGG_OUT)
	cp -r BevFusion/_build/html $(AGG_OUT)/bevfusion
	cp -r FileTree/_build/html $(AGG_OUT)/filetree
	cp -r MultiSensorPostFusion/_build/html $(AGG_OUT)/multisensorpostfusion

all: build aggregate
	python3 merge_search_index.py
	@echo "聚合站点输出目录: $(AGG_OUT)"

clean:
	rm -rf BevFusion/_build FileTree/_build MultiSensorPostFusion/_build aggregate/_build
