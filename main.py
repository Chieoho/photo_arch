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
    QtWidgets, MainWindow
)
from photo_arch.infrastructures.user_interface.qt.interaction.training import Training
from photo_arch.infrastructures.user_interface.qt.interaction.arch_transfer import ArchTransfer
from photo_arch.infrastructures.user_interface.qt.interaction.arch_browser import ArchBrowser
from photo_arch.infrastructures.user_interface.qt.interaction.group_description import GroupDescription
from photo_arch.infrastructures.user_interface.qt.interaction.recognition import Recognition
from photo_arch.infrastructures.user_interface.qt.interaction.photo_description import PhotoDescription
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting
from photo_arch.infrastructures.user_interface.qt.interaction.special import Special

SCALE = 0.786  # 初始窗体宽高和屏幕分辨率的比例


def init_modules(mw_):
    setting = Setting(mw_)
    GroupDescription(mw_, setting)
    Recognition(mw_, setting)
    PhotoDescription(mw_, setting)
    Training(mw_, setting)
    arch_browser = ArchBrowser(mw_, setting)
    arch_transfer = ArchTransfer(mw_, setting)
    Special(mw_, setting, arch_browser, arch_transfer)


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
