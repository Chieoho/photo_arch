# -*- coding: utf-8 -*-
"""
@file: special.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 9:46
"""
import typing

from photo_arch.infrastructures.user_interface.qt.interaction.utils import static
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting, SettingData

from photo_arch.infrastructures.user_interface.qt.interaction.arch_browser import ArchBrowser
from photo_arch.infrastructures.user_interface.qt.interaction.arch_transfer import ArchTransfer


class Special(object):
    def __init__(self,
                 mw_: MainWindow,
                 setting: Setting,
                 arch_browser: ArchBrowser,
                 arch_transfer: ArchTransfer):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.setting = setting

        self.arch_browser = arch_browser
        self.arch_transfer = arch_transfer

        self.ui.tabWidget.currentChanged.connect(static(self.tab_change))

    def tab_change(self, tab_id):
        if tab_id == self.ui.tabWidget.indexOf(self.ui.modeltrain_tab):
            if self.mw.interaction != typing.Any:
                untrained_photo_num = self.mw.interaction.get_untrained_photo_num()
                self.ui.untrained_num_label.setText(str(untrained_photo_num))
        elif tab_id == self.ui.tabWidget.indexOf(self.ui.arch_view_tab):
            _, arch = self.arch_browser.controller.browse_arch()
            self.arch_browser.view.display_browse_arch(arch, self.ui.order_combobox_browse.currentText())
        elif tab_id == self.ui.tabWidget.indexOf(self.ui.arch_transfer_tab):
            _, arch = self.arch_transfer.controller.list_arch()
            self.arch_transfer.view.display_transfer_arch(arch, self.ui.order_combobox_transfer.currentText())

        if tab_id != self.ui.tabWidget.indexOf(self.ui.setting_tab):
            setting_data = SettingData().__dict__
            if not all([getattr(self.setting, k) for k in setting_data]):
                self.ui.tabWidget.setCurrentWidget(self.ui.setting_tab)
                self.mw.msg_box('请完成系统设置')
