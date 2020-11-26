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
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting

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
        if tab_id == 3:  # 选中“模型训练”tab
            if self.mw.interaction != typing.Any:
                untrained_photo_num = self.mw.interaction.get_untrained_photo_num()
                self.ui.untrained_num_label.setText(str(untrained_photo_num))
        elif tab_id == 4:  # 选中“档案浏览”tab
            self.arch_browser.controller.browse_arch()
            self.arch_browser.view.display_browse_arch(self.ui.order_combobox_browse.currentText())
        elif tab_id == 5:  # 选中“档案移交”tab
            self.arch_transfer.controller.list_arch()
            self.arch_transfer.view.display_transfer_arch(self.ui.order_combobox_transfer.currentText())
        else:
            pass
