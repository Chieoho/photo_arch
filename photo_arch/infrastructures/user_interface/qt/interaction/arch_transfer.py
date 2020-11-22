# -*- coding: utf-8 -*-
"""
@file: arch_transfer.py
@desc:
@author: Jaden Wu
@time: 2020/11/22 21:36
"""
import os
import glob
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow,
    static,
    catch_exception,
)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting


class ArchTransfer(object):
    def __init__(self, mw_: MainWindow):
        self.mw = mw_
        self.selected_arch_list = []

        list_widget = self.mw.ui.selected_arch_list_widget
        list_widget.setViewMode(QListWidget.IconMode)
        list_widget.setIconSize(QSize(200, 150))
        list_widget.setResizeMode(QListWidget.Adjust)
        list_widget.itemDoubleClicked.connect(static(self.unselect_arch))

        self.mw.ui.order_combobox_transfer.currentTextChanged.connect(static(self.display_arch))
        self.mw.ui.arch_tree_view_transfer.doubleClicked.connect(static(self.select_arch))

    @catch_exception
    def display_arch(self, text):
        self.mw.ui.order_combobox_browse.setCurrentText(text)
        self.mw.view.display_arch(text)

    @catch_exception
    def select_arch(self, index):
        if index.child(0, 0).data():  # 点击的不是组名则返回
            return
        group_name = index.data()
        if group_name in self.selected_arch_list:
            return
        path = os.path.join(Setting.path, group_name, '*.*')
        for fp in glob.iglob(path):
            item = QListWidgetItem(QIcon(fp), group_name)
            self.mw.ui.selected_arch_list_widget.addItem(item)
            break
        self.selected_arch_list.append(group_name)

    @catch_exception
    def unselect_arch(self, item):
        row = self.mw.ui.selected_arch_list_widget.row(item)
        self.mw.ui.selected_arch_list_widget.takeItem(row)
        item_text = item.text()
        if item_text in self.selected_arch_list:
            self.selected_arch_list.remove(item_text)
