from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QFont
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 中文测试窗口")
        self.resize(400,220)

        # 全局中文字体
        font = QFont("WenQuanYi Zen Hei")
        font.setPointSize(12)
        QApplication.instance().setFont(font)

        # 【核心】创建中心部件 + 垂直布局，替代move绝对坐标
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(60,40,60,40) # 边距 left top right bottom
        layout.setSpacing(30) # 控件之间间距

        self.label = QLabel("中文测试：等待点击")
        self.btn = QPushButton("点击按钮")
        self.btn.clicked.connect(self.on_click)

        # 加入布局，自动排列
        layout.addWidget(self.label)
        layout.addWidget(self.btn)

    def on_click(self):
        self.label.setText("文字更新成功，中文正常显示！")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
