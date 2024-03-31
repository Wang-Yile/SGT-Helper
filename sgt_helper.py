LICENSE = """
    SGT Helper
    Copyright (C) 2024  Yile Wang

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import math

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

try:
    os.chdir(os.path.dirname(sys.argv[0]))
except OSError:
    pass

UI_FONT = QFont(["Consolas", "微软雅黑"], 10)
CODE_FONT = QFont(["Consolas", "微软雅黑"], 10)
NOTE_FONT = QFont(["Consolas", "微软雅黑"], 8)

class Break(Exception):
    def __init__(self, reason: str = ""):
        self.reason = reason
    def __str__(self) -> str:
        return self.reason

class GraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self._scale = 1
    def wheelEvent(self, event):
        angle = event.angleDelta()
        zoomIn = 1.25
        zoomOut = 0.8
        if angle.y() > 0: # 向上 放大
            if self._scale * zoomIn <= 5:
                self._scale *= zoomIn
        else: # 向下 缩小
            self._scale *= zoomOut
        self.setTransform(QTransform.fromScale(self._scale, self._scale))
        return super().wheelEvent(event)
    def rescale(self, scale: float):
        self._scale = scale
        self.setTransform(QTransform.fromScale(self._scale, self._scale))

class SGT_Helper(QMainWindow):
    def __init__(self):
        super().__init__()
        self._sgt_items = []
        self._sgt = []
        self._display_tag = []
        self.init_ui()
    def init_ui(self):
        self.setWindowTitle("SGT Helper - 线段树调试工具")
        self.resize(960, 600)
        self.setFont(UI_FONT)
        self._view = GraphicsView()
        self._scene = QGraphicsScene()
        self._view.setScene(self._scene)
        self._control = QWidget()
        self.init_control()
        self._widget = QWidget()
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(3, 3, 3, 3)
        self._layout.setSpacing(3)
        self._layout.addWidget(self._view)
        self._layout.addWidget(self._control_scroll)
        self._widget.setLayout(self._layout)
        self.setCentralWidget(self._widget)
    def init_control(self):
        self._control_layout = QVBoxLayout()
        self._control_layout.setContentsMargins(0, 0, 0, 0)
        self._control_layout.setSpacing(3)
        self._control.setLayout(self._control_layout)
        self._command = QWidget()
        self._control_layout.addWidget(self._command)
        self.init_command()
        self._control_layout.addWidget(QLabel("内容"))
        label = QLabel("线段树储存的数据，数据以空格分开，每行一组。")
        label.setFont(NOTE_FONT)
        self._control_layout.addWidget(label)
        self._control_input = QTextEdit()
        self._control_input.setFont(CODE_FONT)
        self._control_layout.addWidget(self._control_input)
        self._control_layout.addWidget(QLabel("格式"))
        label = QLabel("逐个为数据命名，每行一个。必须包含表示线段范围的 `s` 和 `t` 名称。")
        label.setFont(NOTE_FONT)
        self._control_layout.addWidget(label)
        self._control_format = QTextEdit()
        self._control_format.setFont(CODE_FONT)
        self._control_format.setText("s\nt")
        self._control_layout.addWidget(self._control_format)
        self._control_layout.addWidget(QLabel("显示的格式"))
        label = QLabel("显示的数据，每行一个。")
        label.setFont(NOTE_FONT)
        self._control_layout.addWidget(label)
        self._control_display = QTextEdit()
        self._control_display.setFont(CODE_FONT)
        self._control_display.setText("")
        self._control_layout.addWidget(self._control_display)
        self._control_layout.addWidget(QLabel("渲染信息"))
        self._control_info = QTextBrowser()
        self._control_info.setFont(CODE_FONT)
        self._control_info.setText("")
        self._control_layout.addWidget(self._control_info)
        self._control_scroll = QScrollArea()
        self._control_scroll.setContentsMargins(3, 3, 3, 3)
        self._control_scroll.setBackgroundRole(QPalette.Light)
        self._control_scroll.setWidgetResizable(True)
        self._control_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._control_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._control_scroll.setWidget(self._control)
    def init_command(self):
        self._command_layout = QHBoxLayout()
        self._command_layout.setContentsMargins(0, 0, 0, 0)
        self._command_layout.setSpacing(0)
        self._command.setLayout(self._command_layout)
        self._command_render = QPushButton("渲染")
        self._command_render.clicked.connect(self.command_render)
        self._command_layout.addWidget(self._command_render)
        self._command_rescale = QPushButton("重置缩放")
        self._command_rescale.clicked.connect(lambda: self._view.rescale(1))
        self._command_layout.addWidget(self._command_rescale)
        self._command_license = QPushButton("发行许可证")
        self._command_license.clicked.connect(self.command_license)
        self._command_layout.addWidget(self._command_license)
    def command_render(self):
        self.sgt_render()
    def command_license(self):
        QMessageBox.about(self, "发行许可证 / License", LICENSE)
    def sgt_render(self):
        scene = self._scene
        for item in self._sgt_items:
            scene.removeItem(item)
        self._control_info.clear()
        self._sgt_items.clear()
        self._sgt.clear()
        self._display_tag.clear()
        for name in self._control_display.toPlainText().splitlines():
            if name:
                self._display_tag.append(name)
        form = []
        for name in self._control_format.toPlainText().splitlines():
            if name:
                form.append(name)
        if "s" not in form or "t" not in form:
            self._control_info.append("[错误] 需要 `s` 和 `t`。\n")
            return
        try:
            seg = []
            for line in self._control_input.toPlainText().splitlines():
                if line:
                    cur = {}
                    index = 0
                    for dt in line.split(sep=" "):
                        if dt:
                            if index >= len(form):
                                self._control_info.append("[错误] 格式错误。\n")
                                raise Break
                            if form[index] == "s" or form[index] == "t":
                                try:
                                    cur[form[index]] = int(dt)
                                except ValueError:
                                    self._control_info.append("[错误] `s` 和 `t` 需要为整数。\n")
                                    raise Break
                            else:
                                cur[form[index]] = dt
                            index += 1
                    if len(cur) != len(form):
                        self._control_info.append("[错误] 格式错误。\n")
                        raise Break
                    seg.append(cur)
        except Break:
            return
        else:
            I_X = 50 # x 轴单位距离
            I_Y = 30 + len(self._display_tag) * 15 # y 轴单位距离
            length = max(seg, key=lambda x: x["t"] - x["s"] + 1)
            length: int = length["t"] - length["s"] + 1
            for segment in seg:
                segment: dict
                s = segment["s"]
                t = segment["t"]
                lenn = t - s + 1
                x1 = s
                x2 = t + 1
                y = int(math.ceil(math.log2(length / lenn))) + 1
                self._sgt_items.append(scene.addLine(x1*I_X + 3, y*I_Y, x2*I_X - 3, y*I_Y, QPen("#000000")))
                self._sgt_items.append(scene.addLine(x1*I_X + 3, y*I_Y, x1*I_X + 3, y*I_Y - 3, QPen("#000000")))
                self._sgt_items.append(scene.addLine(x2*I_X - 3, y*I_Y, x2*I_X - 3, y*I_Y - 3, QPen("#000000")))
                for key in segment.keys():
                    index = 1
                    if key in self._display_tag:
                        value = segment[key]
                        item = scene.addText(f"{key}: {value}", UI_FONT)
                        pos = QPointF((x1*I_X + x2*I_X) / 2, y*I_Y - index*10)
                        delta = QPointF(item.boundingRect().width() / 2, item.boundingRect().height() / 2)
                        item.setPos(pos - delta)
                        self._sgt_items.append(item)
            self._sgt = seg
    def show(self):
        super().show()
        self.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SGT_Helper()
    window.show()
    app.exec()
