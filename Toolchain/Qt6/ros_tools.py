#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROS Toolbox Launcher — PyQt6 多按钮 ROS 工具启动面板
依赖: pip install PyQt6
"""

import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QGroupBox,
    QGridLayout, QMessageBox, QComboBox, QInputDialog
)
from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment
from PyQt6.QtGui import QFont, QTextCursor


# 备用工具按钮配置：(显示名, 可执行命令, 备注)
EXTRA_TOOLS = [
    ("rqt_graph",   "rqt_graph",   "节点/话题关系图"),
    ("rqt_plot",    "rqt_plot",    "话题曲线实时绘图"),
    ("rqt_console", "rqt_console", "rosout 日志查看"),
    ("rqt_reconfigure", "rosrun rqt_reconfigure rqt_reconfigure", "动态参数调参"),
    ("rosbag record", "rosbag record -a -O bag", "录制所有话题"),
    ("rostopic list", "bash -lc 'source /opt/ros/noetic/setup.bash && rostopic list'", "列话题"),
]


class RosToolbox(QMainWindow):
    def __init__(self):
        super().__init__()
        # 每个功能一个独立 QProcess，按 key 管理
        self.procs = {}        # key -> QProcess
        self.log_buffers = {}  # key -> str (每个进程的日志缓冲)
        self.current_log_key = None

        self.init_ui()
        self.refresh_packages()

    # ---------------- UI ----------------
    def init_ui(self):
        self.setWindowTitle("ROS Toolbox Launcher")
        self.resize(860, 640)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # ===== 1. roscore 主控 =====
        master_box = QGroupBox("① ROS Master")
        ml = QHBoxLayout(master_box)

        self.master_dot = QLabel("●")
        self.master_dot.setStyleSheet("color:#888;font-size:18px;")
        ml.addWidget(self.master_dot)
        self.master_status = QLabel("roscore 未启动")
        self.master_status.setStyleSheet("font-weight:bold;")
        ml.addWidget(self.master_status)
        ml.addStretch(1)

        ml.addWidget(QLabel("URI:"))
        self.uri_edit = QLineEdit("http://localhost:11311")
        self.uri_edit.setFixedWidth(180)
        ml.addWidget(self.uri_edit)

        self.btn_roscore = QPushButton("启动 roscore")
        self.btn_roscore.setStyleSheet(
            "QPushButton{padding:6px 16px;background:#2e7d32;color:white;border-radius:4px;font-weight:bold;}"
            "QPushButton:hover{background:#388e3c;}"
            "QPushButton:disabled{background:#9e9e9e;}"
        )
        self.btn_roscore.clicked.connect(self.toggle_roscore)
        ml.addWidget(self.btn_roscore)
        root.addWidget(master_box)

        # ===== 2. 可视化工具按钮组 =====
        viz_box = QGroupBox("② 可视化 / 调试工具（点击即启动，再点停止）")
        vgl = QGridLayout(viz_box)

        self.btn_map = {}  # key -> button
        viz_buttons = [
            ("rviz",  "rviz",            "3D 可视化"),
        ]
        # 加上备用工具
        viz_buttons += [(name, cmd, desc) for (name, cmd, desc) in EXTRA_TOOLS]

        for i, (key, cmd, desc) in enumerate(viz_buttons):
            btn = QPushButton(f"{key}\n{desc}")
            btn.setCheckable(True)
            btn.setMinimumHeight(48)
            btn.clicked.connect(lambda checked, k=key, c=cmd: self.toggle_tool(k, c, checked))
            vgl.addWidget(btn, i // 3, i % 3)
            self.btn_map[key] = btn
        root.addWidget(viz_box)

        # ===== 3. 选包 roslaunch / rosrun =====
        pkg_box = QGroupBox("③ 选择 ROS 包并启动 launch / node")
        pl = QGridLayout(pkg_box)

        pl.addWidget(QLabel("Package:"), 0, 0)
        self.pkg_combo = QComboBox()
        self.pkg_combo.setEditable(True)
        self.pkg_combo.setMinimumWidth(320)
        pl.addWidget(self.pkg_combo, 0, 1)

        self.btn_refresh_pkg = QPushButton("刷新包列表")
        self.btn_refresh_pkg.clicked.connect(self.refresh_packages)
        pl.addWidget(self.btn_refresh_pkg, 0, 2)

        pl.addWidget(QLabel("Launch 文件:"), 1, 0)
        self.launch_edit = QLineEdit("")
        self.launch_edit.setPlaceholderText("如: my_nav  map_server.launch  （留空则按 rosrun 方式）")
        pl.addWidget(self.launch_edit, 1, 1, 1, 2)

        self.btn_launch = QPushButton("roslaunch 启动")
        self.btn_launch.setStyleSheet(
            "QPushButton{padding:6px 14px;background:#1565c0;color:white;border-radius:4px;}"
            "QPushButton:hover{background:#1976d2;}"
        )
        self.btn_launch.clicked.connect(self.start_launch)
        pl.addWidget(self.btn_launch, 2, 0)

        self.btn_run = QPushButton("rosrun 启动节点")
        self.btn_run.setStyleSheet(
            "QPushButton{padding:6px 14px;background:#6a1b9a;color:white;border-radius:4px;}"
            "QPushButton:hover{background:#7b1fa2;}"
        )
        self.btn_run.clicked.connect(self.start_run)
        pl.addWidget(self.btn_run, 2, 1)
        root.addWidget(pkg_box)

        # ===== 4. 日志区 =====
        log_box = QGroupBox("④ 日志输出（选择进程查看）")
        ll = QVBoxLayout(log_box)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("查看:"))
        self.log_combo = QComboBox()
        self.log_combo.addItem("roscore")
        self.log_combo.setCurrentText("roscore")
        self.log_combo.currentTextChanged.connect(self.switch_log_view)
        bar.addWidget(self.log_combo)
        bar.addStretch(1)
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(lambda: self.clear_current_log())
        bar.addWidget(clear_btn)
        ll.addLayout(bar)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Menlo, Consolas, monospace", 9))
        self.log.setStyleSheet("background:#1e1e1e;color:#d4d4d4;")
        ll.addWidget(self.log)
        root.addWidget(log_box, stretch=1)

        self.current_log_key = "roscore"

    # ---------------- 包列表 ----------------
    def refresh_packages(self):
        """调用 rospack list 拉取所有包名"""
        self.pkg_combo.clear()
        try:
            r = subprocess.run(
                ["bash", "-lc", "source /opt/ros/noetic/setup.bash && rospack list 2>/dev/null"],
                capture_output=True, text=True, timeout=5
            )
            pkgs = [line.split()[0] for line in r.stdout.strip().splitlines() if line.strip()]
            self.pkg_combo.addItems(pkgs)
            self._log(f"[GUI] 已加载 {len(pkgs)} 个 ROS 包", "#6a9955")
        except Exception as e:
            self._log(f"[GUI] 拉取包列表失败: {e}（可手动输入包名）", "#f48771")

    # ---------------- 进程管理 ----------------
    def _make_proc(self, key: str) -> QProcess:
        env = QProcessEnvironment.systemEnvironment()
        # 注入当前 UI 上的 URI / IP
        uri = self.uri_edit.text().strip()
        if uri:
            env.insert("ROS_MASTER_URI", uri)
        p = QProcess(self)
        p.setProcessEnvironment(env)
        p.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        p.readyReadStandardOutput.connect(lambda k=key: self._on_read(k))
        p.finished.connect(lambda code, st, k=key: self._on_finished(k, code, st))
        self.procs[key] = p
        self.log_buffers.setdefault(key, "")
        return p

    def _start(self, key: str, cmd: str):
        if key in self.procs and self.procs[key].state() != QProcess.ProcessState.NotRunning:
            return
        p = self._make_proc(key)
        self._log(f"[GUI] >>> 启动 [{key}]: {cmd}", "#dcdcaa")
        # 用 bash -lc 包装，确保拿到 ROS 环境
        p.start("bash", ["-lc", cmd])
        # 同步日志下拉框
        if self.log_combo.findText(key) < 0:
            self.log_combo.addItem(key)

    def _stop(self, key: str):
        p = self.procs.get(key)
        if not p or p.state() == QProcess.ProcessState.NotRunning:
            return
        self._log(f"[GUI] <<< 停止 [{key}]", "#dcdcaa")
        p.terminate()
        if not p.waitForFinished(2500):
            p.kill()

    # ---- roscore ----
    def toggle_roscore(self):
        p = self.procs.get("roscore")
        if p and p.state() != QProcess.ProcessState.NotRunning:
            self._stop("roscore")
        else:
            self._start("roscore", "roscore")

    # ---- 工具按钮 ----
    def toggle_tool(self, key: str, cmd: str, checked: bool):
        if checked:
            self._start(key, cmd)
        else:
            self._stop(key)

    # ---- roslaunch / rosrun ----
    def start_launch(self):
        pkg = self.pkg_combo.currentText().strip()
        launch = self.launch_edit.text().strip()
        if not pkg or not launch:
            QMessageBox.warning(self, "缺参数", "请填写 Package 和 Launch 文件")
            return
        key = f"launch:{pkg}/{launch}"
        self._start(key, f"roslaunch {pkg} {launch}")
        self.log_combo.addItem(key)

    def start_run(self):
        pkg = self.pkg_combo.currentText().strip()
        node, ok = QInputDialog.getText(self, "rosrun", "节点可执行文件名:")
        if not ok or not node.strip():
            return
        key = f"run:{pkg}/{node.strip()}"
        self._start(key, f"rosrun {pkg} {node.strip()}")
        self.log_combo.addItem(key)

    # ---------------- 回调 ----------------
    def _on_read(self, key: str):
        p = self.procs[key]
        data = bytes(p.readAllStandardOutput()).decode("utf-8", errors="replace")
        self.log_buffers[key] = self.log_buffers.get(key, "") + data
        if self.current_log_key == key:
            self.log.moveCursor(QTextCursor.MoveOperation.End)
            self.log.insertPlainText(data)

    def _on_finished(self, key: str, code, status):
        self._log(f"[GUI] 进程 [{key}] 退出 code={code}", "#f48771")
        if key == "roscore":
            self.master_dot.setStyleSheet("color:#888;font-size:18px;")
            self.master_status.setText("roscore 未启动")
            self.btn_roscore.setText("启动 roscore")
            self.btn_roscore.setStyleSheet(
                "QPushButton{padding:6px 16px;background:#2e7d32;color:white;border-radius:4px;font-weight:bold;}"
                "QPushButton:hover{background:#388e3c;}"
            )
        if key in self.btn_map:
            self.btn_map[key].setChecked(False)

    # ---------------- 日志显示 ----------------
    def _log(self, text: str, color: str = "#6a9955"):
        key = self.current_log_key or "roscore"
        self.log_buffers[key] = self.log_buffers.get(key, "") + text + "\n"
        self.log.append(f'<span style="color:{color}">{text}</span>')

    def switch_log_view(self, key: str):
        self.current_log_key = key
        self.log.clear()
        self.log.setHtml(f'<div style="color:#888">--- {key} 日志 ---</div>')
        self.log.append(f'<span style="color:#d4d4d4">{self.log_buffers.get(key, "")}</span>')

    def clear_current_log(self):
        if self.current_log_key:
            self.log_buffers[self.current_log_key] = ""
        self.log.clear()

    # ---------------- 关闭 ----------------
    def closeEvent(self, e):
        running = [k for k, p in self.procs.items() if p.state() != QProcess.ProcessState.NotRunning]
        if running:
            ret = QMessageBox.question(self, "退出",
                f"以下进程仍在运行:\n{chr(10).join(running)}\n\n全部停止并退出？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ret != QMessageBox.StandardButton.Yes:
                e.ignore(); return
            for k in running:
                self._stop(k)
        e.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = RosToolbox()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
