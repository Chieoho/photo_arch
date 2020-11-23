# -*- coding: utf-8 -*-
"""
@file: arch_transfer.py
@desc:
@author: Jaden Wu
@time: 2020/11/22 21:36
"""
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, View,
    static, catch_exception,
)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting


class ArchTransfer(object):
    def __init__(self, mw_: MainWindow, setting: Setting, view: View):
        self.mw = mw_
        self.setting = setting
        self.view = view

        self.selected_arch_list = []
        # self.disk_icon_path = './icon/disk.png'
        self.disk_icon_path = './icon/arch_cd.png'

        self.mw.ui.partition_list_widget.setViewMode(QListWidget.IconMode)
        self.mw.ui.partition_list_widget.setIconSize(QSize(200, 150))

        self.mw.ui.order_combobox_transfer.currentTextChanged.connect(static(self.display_arch))
        self.mw.ui.arch_tree_view_transfer.doubleClicked.connect(static(self.select_arch))
        self.mw.ui.selected_arch_list_widget.itemDoubleClicked.connect(static(self.unselect_arch))
        self.mw.ui.disk_size_line_edit.returnPressed.connect(static(self.partition))
        self.mw.ui.across_year_combo_box.currentTextChanged.connect(static(self.partition))
        self.mw.ui.across_period_combo_box.currentTextChanged.connect(static(self.partition))

    @catch_exception
    def display_arch(self, text):
        self.view.display_transfer_arch(text)

    @catch_exception
    def select_arch(self, index):
        if index.child(0, 0).data():  # 点击的不是叶子则返回
            return
        parent_index = index.parent()
        fonds_code_index = parent_index.parent()
        selected_name = '-'.join([fonds_code_index.data(), parent_index.data(), index.data()])
        if selected_name in self.selected_arch_list:
            return
        item = QListWidgetItem(selected_name)
        self.mw.ui.selected_arch_list_widget.addItem(item)
        self.selected_arch_list.append(selected_name)
        self.partition()

    @catch_exception
    def unselect_arch(self, item):
        row = self.mw.ui.selected_arch_list_widget.row(item)
        self.mw.ui.selected_arch_list_widget.takeItem(row)
        item_text = item.text()
        if item_text in self.selected_arch_list:
            self.selected_arch_list.remove(item_text)
        self.partition()

    @catch_exception
    def partition(self):
        self.mw.ui.partition_list_widget.clear()
        disk_size = self.mw.ui.disk_size_line_edit.text()
        if (not disk_size) or (not self.selected_arch_list):
            return
        item = QListWidgetItem(QIcon(self.disk_icon_path), 'disk 1(A1-2018-30年)')
        self.mw.ui.partition_list_widget.addItem(item)
