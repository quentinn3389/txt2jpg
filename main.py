#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TXT → 320×240 灰度 JPG（3 图循环，年月日时分秒命名）
打包：
    pyinstaller -F -w txt2jpg.py
"""
import sys, re, time
from pathlib import Path
# 修改导入语句：PyQt5 -> PyQt6
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton,
                             QVBoxLayout, QHBoxLayout, QFileDialog,
                             QLabel, QMessageBox)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt  # 显式导入 Qt
from PIL import Image


def hex_txt_to_bytes(hex_txt: str) -> bytes:
    hex_clean = re.sub(r'[^0-9A-Fa-f]', '', hex_txt)
    if len(hex_clean) != 76800 * 2:
        raise ValueError(f"需要 76800 字节，实际 {len(hex_clean) // 2} 字节")
    return bytes.fromhex(hex_clean)


def bytes_to_gray_jpg(data: bytes, save_path: str):
    img = Image.frombuffer('L', (320, 240), data, 'raw', 'L', 0, 1)
    img.save(save_path, quality=95)


class Win(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TXT → 320×240 JPG（3 张循环）")
        self.resize(650, 280)

        # 1. 创建按钮
        self.btn = QPushButton("导入 txt")
        # 2. 取当前字体平均宽度做基准（1 字符 ≈ 8 px，高度 ≈ 25 px）
        fm = self.btn.fontMetrics()
        char_w = fm.averageCharWidth()
        line_h = fm.height()
        # 3. 原按钮大约 14 字符宽，现在 1/5 → 3 字符；高度 ×2 → 2 行高
        self.btn.setFixedSize(int(char_w * 3), int(line_h * 2))

        self.img_labels = [QLabel("(图片将显示在这里)") for _ in range(3)]
        for lbl in self.img_labels:
            lbl.setMinimumSize(320, 240)
            lbl.setScaledContents(True)

        self.btn = QPushButton("导入 txt 文件")
        self.btn.clicked.connect(self.load_txt)

        hbox = QHBoxLayout()
        for lbl in self.img_labels:
            hbox.addWidget(lbl)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.btn, stretch=0)
        vbox.addLayout(hbox, stretch=1)

        self._idx = 0
        self.jpg_paths = [None, None, None]

    def load_txt(self):
        # PyQt6 中 QFileDialog 的返回值略有变化
        path, _ = QFileDialog.getOpenFileName(self, "选择 hex 文本", "", "*.txt")
        if not path:
            return
        try:
            data = Path(path).read_text(encoding='utf-8', errors='ignore')
            raw = hex_txt_to_bytes(data)

            # 年月日时分秒命名
            name = time.strftime("%Y%m%d_%H%M%S") + ".jpg"
            jpg_path = str(Path(path).parent / name)

            bytes_to_gray_jpg(raw, jpg_path)
        except Exception as e:
            # PyQt6 中消息框的枚举值可能需要调整，但此处使用的标准方法通常兼容
            QMessageBox.critical(self, "出错了", str(e))
            return

        pixmap = QPixmap(jpg_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "错误", f"无法加载图片: {jpg_path}")
            return

        self.img_labels[self._idx].setPixmap(pixmap)
        self.jpg_paths[self._idx] = jpg_path
        self._idx = (self._idx + 1) % 3
        # QMessageBox.information(self, "完成", f"已生成并保存为\n{jpg_path}")


if __name__ == '__main__':
    # PyQt6 中的应用执行入口改为 exec() 而不是 exec_()
    app = QApplication(sys.argv)
    w = Win()
    w.show()
    sys.exit(app.exec())  # 注意这里改为 exec()