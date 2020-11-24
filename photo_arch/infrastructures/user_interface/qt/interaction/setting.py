# -*- coding: utf-8 -*-
"""
@file: setting.py
@desc:
@author: Jaden Wu
@time: 2020/11/23 9:58
"""
import os
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow, View
)


class Setting(object):
    def __init__(self, mw_: MainWindow, view: View):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.view = view

        self.description_path = ''
        self.package_path = ''

        self._get_setting()

    def _get_setting(self):
        self.description_path = r'.\已著录'
        self.package_path = r'.\已打包'
        self.view.display_setting(
            os.path.abspath(self.description_path),
            os.path.abspath(self.package_path)
        )
