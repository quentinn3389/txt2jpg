#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TXT → 320×240 灰度 JPG（6 图循环，2 行 3 列，最新图红框）
打包：
    pyinstaller -F -w txt2jpg.py
"""
import sys, re, time, os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton,
                             QVBoxLayout, QHBoxLayout, QFileDialog,
                             QLabel, QMessageBox, QGridLayout)
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt6.QtCore import Qt
from PIL import Image


# ---------- 工具函数 ----------
def hex_txt_to_bytes(hex_txt: str) -> bytes:
    hex_clean = re.sub(r'[^0-9A-Fa-f]', '', hex_txt)
    if len(hex_clean) != 76800 * 2:
        raise ValueError(f"需要 76800 字节，实际 {len(hex_clean) // 2} 字节")
    return bytes.fromhex(hex_clean)


def bytes_to_gray_jpg(data: bytes, save_path: str):
    img = Image.frombuffer('L', (320, 240), data, 'raw', 'L', 0, 1)
    img.save(save_path, quality=95)


# ---------- 带红框的 QLabel ----------
class BorderedLabel(QLabel):
    """支持开关红色边框的 QLabel"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._draw_border = False
        self.setMinimumSize(320, 240)
        self.setScaledContents(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: black;")  # 无图时黑色背景

    def set_border_enabled(self, enable: bool):
        self._draw_border = enable
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._draw_border:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 0, 0), 4))
            painter.drawRect(self.rect())


# ---------- 主窗口 ----------
class Win(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TXT → 320×240 JPG（6 张循环，2×3）")
        self.resize(1000, 650)

        # 1. 按钮
        fm = QPushButton().fontMetrics()
        btn_w = int(fm.averageCharWidth() * 20)
        btn_h = int(fm.height() * 4)

        self.import_btn = QPushButton("导入 txt 文件")
        self.import_btn.setFixedSize(btn_w, btn_h)
        self.import_btn.clicked.connect(self.load_txt)

        self.clear_btn = QPushButton("清除所有照片")
        self.clear_btn.setFixedSize(btn_w, btn_h)
        self.clear_btn.clicked.connect(self.clear_all)

        # 2. 图片标签 + 文字标签
        self.img_labels = [BorderedLabel() for _ in range(6)]
        self.txt_labels = [QLabel(f"({i+1})") for i in range(6)]
        for txt in self.txt_labels:
            txt.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.jpg_paths = [None] * 6
        self._idx = 0

        # 3. 2×3 网格：文字行 0/2，图片行 1/3
        grid = QGridLayout()
        for c in range(3):
            grid.addWidget(self.txt_labels[c],   0, c)
            grid.addWidget(self.img_labels[c],   1, c)
        for c in range(3):
            grid.addWidget(self.txt_labels[c+3], 2, c)
            grid.addWidget(self.img_labels[c+3], 3, c)

        # 4. 按钮水平布局
        h_btn = QHBoxLayout()
        h_btn.addWidget(self.import_btn)
        h_btn.addWidget(self.clear_btn)
        h_btn.addStretch()

        # 5. 总布局
        vbox = QVBoxLayout(self)
        vbox.addLayout(h_btn)
        vbox.addLayout(grid, stretch=1)

        # 6. 输出目录
        self.out_dir = Path(sys.executable).parent / "output" \
            if getattr(sys, 'frozen', False) else Path(__file__).parent / "output"
        self.out_dir.mkdir(exist_ok=True)

        # 7. 默认白底
        for lbl in self.img_labels:
            lbl.setStyleSheet("background-color: white;")

    # ---------- 导入 ----------
    def load_txt(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 hex 文本", "", "*.txt")
        if not path:
            return
        try:
            data = Path(path).read_text(encoding='utf-8', errors='ignore')
            raw = hex_txt_to_bytes(data)
            name = time.strftime("%Y%m%d_%H%M%S") + ".jpg"
            jpg_path = str(self.out_dir / name)
            bytes_to_gray_jpg(raw, jpg_path)
        except Exception as e:
            QMessageBox.critical(self, "出错了", str(e))
            return

        pixmap = QPixmap(jpg_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "错误", f"无法加载图片: {jpg_path}")
            return

        # 去红框 -> 写图 -> 加红框 -> 更新文字
        for lbl in self.img_labels:
            lbl.set_border_enabled(False)

        self.img_labels[self._idx].setPixmap(pixmap)
        self.img_labels[self._idx].set_border_enabled(True)
        self.jpg_paths[self._idx] = jpg_path
        self.txt_labels[self._idx].setText(
            f"({self._idx + 1})  {time.strftime('%m-%d %H:%M:%S')}"
        )
        self._idx = (self._idx + 1) % 6

    # ---------- 清除 ----------
    def clear_all(self):
        for i in range(6):
            self.img_labels[i].clear()
            self.img_labels[i].set_border_enabled(False)
            self.txt_labels[i].setText(f"({i+1})")
            self.jpg_paths[i] = None
        self._idx = 0

# ---------- 入口 ----------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Win()
    w.show()
    sys.exit(app.exec())
