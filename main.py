# -*- coding: utf-8 -*-
"""
@file: main.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 16:43
"""
import sys
from photo_arch.infrastructures.gui.qt_gui import QtWidgets, MainWindow, init_parts
from photo_arch.infrastructures.gui import qt_gui


SCALE = 0.786  # 初始窗体宽高和屏幕分辨率的比例


def main():
    app = QtWidgets.QApplication(sys.argv)
    mw = qt_gui.mw = MainWindow(app)
    mw.resize(int(mw.dt_width*SCALE), int(mw.dt_height*SCALE))
    init_parts(mw)
    mw.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
