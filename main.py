# -*- coding: utf-8 -*-
"""
@file: main.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 16:43
"""
import sys
from photo_arch.infrastructures.gui.qt_gui import QtWidgets, MainWindow, SCALE, init_parts


def main():
    app = QtWidgets.QApplication(sys.argv)
    desktop = app.desktop()
    dt_width_, dt_height_ = desktop.width(), desktop.height()
    mw = MainWindow(dt_width_, dt_height_)
    mw.resize(int(dt_width_*SCALE), int(dt_height_*SCALE))
    init_parts()
    mw.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
