# -*- coding: utf-8 -*-
"""
@file: setting.py
@desc:
@author: Jaden Wu
@time: 2020/11/23 9:58
"""
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, View
)


class Setting(object):
    def __init__(self, mw_: MainWindow, view: View):
        self.mw = mw_
        self.view = view

        self.description_path = ''

        self._get_setting()

    def _get_setting(self):
        self.description_path = r'.\已著录'
