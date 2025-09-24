import sys
import os
import psutil
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QListWidget, QLabel, QProgressBar, QFileDialog, QHBoxLayout
)
from PyQt5.QtCore import QTimer

# QtCore.__file__ 指向 PyQt5 的安装目录
plugin_path = os.path.join(os.path.dirname(QtCore.__file__), "Qt5", "plugins", "platforms")
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path


class DiskMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("磁盘监控工具 (PyQt5)")
        self.resize(400, 300)

        # 半透明窗口
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        self.config_file = "drives.txt"
        self.drive_widgets = {}

        # 主布局
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)

        # ====== 上方区域（按钮 + 列表）======
        top_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("添加盘符")
        self.remove_button = QPushButton("移除盘符")
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        top_layout.addLayout(button_layout)

        # 设置按钮样式
        button_style = """
        QPushButton {
            border: 1px solid #888;
            border-radius: 6px;
            background-color: #E1E1E1;
            padding: 4px 10px;
        }
        QPushButton:hover {
            background-color: #D0D0D0;
        }
        QPushButton:pressed {
            background-color: #C0C0C0;
        }
        """
        self.add_button.setStyleSheet(button_style)
        self.remove_button.setStyleSheet(button_style)

        # 列表
        self.listbox = QListWidget()
        self.listbox.setFixedHeight(100)
        top_layout.addWidget(self.listbox)

        layout.addLayout(top_layout)

        # 磁盘信息容器
        self.panel = QVBoxLayout()
        layout.addLayout(self.panel)

        # 绑定按钮事件
        self.add_button.clicked.connect(self.add_drive_dialog)
        self.remove_button.clicked.connect(self.remove_drive)

        # 读取配置
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                for line in f:
                    self.add_drive(line.strip())

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_drives)
        self.timer.start(3000)  # 每 3 秒刷新

    # 鼠标拖动窗口
    def mousePressEvent(self, event):
        self._old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if hasattr(self, "_old_pos") and self._old_pos:
            delta = event.globalPos() - self._old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self._old_pos = None

    def add_drive_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "选择盘符根目录")
        if folder:
            drive = os.path.splitdrive(folder)[0] + "\\"
            self.add_drive(drive)
            self.save_config()

    def add_drive(self, drive):
        if drive in self.drive_widgets:
            return

        self.listbox.addItem(drive)

        label = QLabel()
        label.setStyleSheet("font: 10pt Segoe UI; color: #333;")
        bar = QProgressBar()
        bar.setFixedHeight(20)
        bar.setTextVisible(False)  # 不显示默认文字
        bar.setStyleSheet(self.progress_style(0))  # 初始样式

        self.panel.addWidget(label)
        self.panel.addWidget(bar)

        self.drive_widgets[drive] = (bar, label)
        self.update_drive(drive)

    def progress_style(self, percent):
        """返回进度条的 QSS 样式"""
        if percent >= 90:
            color = "#E74C3C"  # 红色警告
        else:
            color = "#0078D7"  # 蓝色填充（Win10/11风格）

        return f"""
        QProgressBar {{
            border: 1px solid #888;
            border-radius: 6px;
            background-color: #DDD;
        }}
        QProgressBar::chunk {{
            border-radius: 6px;
            background-color: {color};
        }}
        """

    def update_drives(self):
        for drive in list(self.drive_widgets.keys()):
            self.update_drive(drive)

    def update_drive(self, drive):
        try:
            usage = psutil.disk_usage(drive)
            free = usage.free
            total = usage.total
            percent = usage.percent

            bar, label = self.drive_widgets[drive]
            bar.setValue(int(percent))
            bar.setStyleSheet(self.progress_style(percent))
            label.setText(f"{drive} 剩 {self.format_size(free)} / 共 {self.format_size(total)} ({percent:.1f}% 已用)")

        except Exception:
            if drive in self.drive_widgets:
                bar, label = self.drive_widgets[drive]
                bar.setValue(0)
                bar.setStyleSheet(self.progress_style(0))
                label.setText(f"{drive} 无法读取")

    def remove_drive(self):
        item = self.listbox.currentItem()
        if not item:
            return

        drive = item.text()
        if drive in self.drive_widgets:
            bar, label = self.drive_widgets[drive]
            bar.deleteLater()
            label.deleteLater()
            del self.drive_widgets[drive]

        self.listbox.takeItem(self.listbox.row(item))
        self.save_config()

    def save_config(self):
        drives = [self.listbox.item(i).text() for i in range(self.listbox.count())]
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write("\n".join(drives))

    @staticmethod
    def format_size(bytes_value):
        size = float(bytes_value)
        if size < 1024 ** 3:
            return f"{size / 1024 ** 2:.1f} MB"
        elif size < 1024 ** 4:
            return f"{size / 1024 ** 3:.1f} GB"
        else:
            return f"{size / 1024 ** 4:.2f} TB"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiskMonitor()
    window.show()
    sys.exit(app.exec_())
