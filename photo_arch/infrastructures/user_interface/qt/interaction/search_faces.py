# -*- coding: utf-8 -*-
"""
@file: search_faces.py
@desc:
@author:
@time: 2020/12/7 10:01
"""
# from photo_arch.infrastructures.user_interface.qt.interaction.utils import static
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting


class SearchFaces(object):
    def __init__(self, mw_: MainWindow, setting: Setting):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.setting = setting

        # self.ui.xx_btn.clicked.connect(static(self.slot_func))  # 槽函数前要加static函数

    # def slot_func(self):
    #     self.mw.interaction.xx()  # self.mw.interaction是QtInteraction的实例
