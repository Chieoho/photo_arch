# -*- coding: utf-8 -*-
"""
@file: special.py
@desc: 其他特殊功能
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
        if tab_id == self.ui.tabWidget.indexOf(self.ui.training_tab):
            if self.mw.interaction != typing.Any:
                untrained_photo_num = self.mw.interaction.get_untrained_photo_num()
                self.ui.untrained_num_label.setText(str(untrained_photo_num))
        elif tab_id == self.ui.tabWidget.indexOf(self.ui.arch_browser_tab):
            _, arch = self.arch_browser.controller.browse_arch()
            priority_key = self.ui.order_combobox_browse.currentText()
            self.arch_browser.view.display_browse_arch(arch, priority_key)
        elif tab_id == self.ui.tabWidget.indexOf(self.ui.arch_transfer_tab):
            _, arch = self.arch_transfer.controller.list_arch()
            priority_key = self.ui.order_combobox_transfer.currentText()
            self.arch_transfer.view.display_transfer_arch(arch, priority_key)
        else:
            pass

        if tab_id != self.ui.tabWidget.indexOf(self.ui.setting_tab):
            if self.setting.lic_ctrl_info.is_import is False:
                self.ui.tabWidget.setCurrentWidget(self.ui.setting_tab)
                self.mw.warn_msg('未导入license，请导入有效license')
                return
            if self.setting.lic_ctrl_info.is_exist is False:
                self.ui.tabWidget.setCurrentWidget(self.ui.setting_tab)
                self.mw.warn_msg('license不存在，请导入有效license')
                return
            if self.setting.lic_ctrl_info.is_valid is False:
                self.ui.tabWidget.setCurrentWidget(self.ui.setting_tab)
                self.mw.warn_msg('license无效，请导入有效license')
                return
            if self.setting.lic_ctrl_info.remaining_days <= 0:
                self.ui.tabWidget.setCurrentWidget(self.ui.setting_tab)
                self.mw.warn_msg('license已到期，请导入有效license')
                return
            setting_data = SettingData().__dict__
            if not all([getattr(self.setting, k) for k in setting_data]):
                self.ui.tabWidget.setCurrentWidget(self.ui.setting_tab)
                self.mw.warn_msg('请完成系统设置')
