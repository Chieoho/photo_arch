# -*- coding: utf-8 -*-
"""
@file: main.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 16:43
"""
import sys
from photo_arch.infrastructures.user_interface.qt.interaction import main_window
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    QtWidgets,
    MainWindow,
    Recognition,
    PhotoDescription,
    GroupDescription,
)
from photo_arch.infrastructures.user_interface.qt.interaction.training import Training
from photo_arch.infrastructures.user_interface.qt.interaction.arch_transfer import ArchTransfer
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting
from photo_arch.infrastructures.user_interface.qt.interaction.arch_browser import ArchBrowser

SCALE = 0.786  # 初始窗体宽高和屏幕分辨率的比例


def init_modules(mw_):
    Recognition()
    PhotoDescription()
    GroupDescription()
    Training(mw_)
    ArchBrowser(mw_)
    ArchTransfer(mw_)
    Setting()


def main():
    app = QtWidgets.QApplication(sys.argv)
    mw = main_window.mw = MainWindow(app)
    mw.resize(int(mw.dt_width*SCALE), int(mw.dt_height*SCALE))
    ax = int((mw.dt_width - mw.width()) / 2)
    ay = int((mw.dt_height - mw.height()) / 2) - 100
    mw.move(ax, ay)
    init_modules(mw)
    mw.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
