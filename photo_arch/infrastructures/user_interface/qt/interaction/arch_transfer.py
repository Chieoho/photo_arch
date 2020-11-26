# -*- coding: utf-8 -*-
"""
@file: arch_transfer.py
@desc:
@author: Jaden Wu
@time: 2020/11/22 21:36
"""
from collections import defaultdict

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from photo_arch.infrastructures.user_interface.qt.interaction.utils import static
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting

from photo_arch.infrastructures.databases.db_setting import engine, make_session
from photo_arch.adapters.sql.repo import Repo
from photo_arch.adapters.controller.arch_transfer import Controller
from photo_arch.adapters.presenter.arch_transfer import Presenter
from photo_arch.adapters.view_model.arch_transfer import ViewModel


class View(object):
    def __init__(self, mw_: MainWindow, view_model: ViewModel):
        self.mw = mw_
        self.view_model = view_model

    def _fill_model_from_dict(self, parent, d):
        if isinstance(d, dict):
            for k, v in d.items():
                child = QStandardItem(str(k))
                parent.appendRow(child)
                self._fill_model_from_dict(child, v)
        elif isinstance(d, list):
            for v in d:
                self._fill_model_from_dict(parent, v)
        else:
            parent.appendRow(QStandardItem(str(d)))

    def display_transfer_arch(self, priority_key='年度'):
        data = defaultdict(lambda: defaultdict(dict))
        for gi in self.view_model.arch:
            fc = gi.get('fonds_code')
            ye = gi.get('year')
            rp = gi.get('retention_period')
            if priority_key == '年度':
                data[fc][ye] = rp
            else:
                data[fc][rp] = ye
        model = QStandardItemModel()
        model.setHorizontalHeaderItem(0, QStandardItem("照片档案"))
        self._fill_model_from_dict(model.invisibleRootItem(), data)
        self.mw.ui.arch_tree_view_transfer.setModel(model)
        self.mw.ui.arch_tree_view_transfer.expandAll()


class ArchTransfer(object):
    def __init__(self, mw_: MainWindow, setting: Setting):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.setting = setting
        self.view_model = ViewModel()
        self.presenter = Presenter(self.view_model)
        self.controller = Controller(Repo(make_session(engine)), self.presenter)
        self.view = View(mw_, self.view_model)

        self.selected_arch_list = []
        self.disk_icon_path = './icon/arch_cd.png'

        self.ui.partition_list_widget.setViewMode(QListWidget.IconMode)
        self.ui.partition_list_widget.setIconSize(QSize(200, 150))

        self.ui.order_combobox_transfer.currentTextChanged.connect(static(self.display_arch))
        self.ui.arch_tree_view_transfer.doubleClicked.connect(static(self.select_arch))
        self.ui.selected_arch_list_widget.itemDoubleClicked.connect(static(self.unselect_arch))
        self.ui.disk_size_line_edit.returnPressed.connect(static(self.partition))
        self.ui.across_year_combo_box.currentTextChanged.connect(static(self.partition))
        self.ui.across_period_combo_box.currentTextChanged.connect(static(self.partition))

    def display_arch(self, text):
        self.view.display_transfer_arch(text)

    def select_arch(self, index):
        if index.child(0, 0).data():  # 点击的不是叶子则返回
            return
        parent_index = index.parent()
        fonds_code_index = parent_index.parent()
        selected_name1 = '-'.join([fonds_code_index.data(), parent_index.data(), index.data()])
        selected_name2 = '-'.join([fonds_code_index.data(), index.data(), parent_index.data()])
        if (selected_name1 in self.selected_arch_list) or \
                (selected_name2 in self.selected_arch_list):
            return
        item = QListWidgetItem(selected_name1)
        self.ui.selected_arch_list_widget.addItem(item)
        self.selected_arch_list.append(selected_name1)
        self.partition()

    def unselect_arch(self, item):
        row = self.ui.selected_arch_list_widget.row(item)
        self.ui.selected_arch_list_widget.takeItem(row)
        item_text = item.text()
        if item_text in self.selected_arch_list:
            self.selected_arch_list.remove(item_text)
        self.partition()

    def partition(self):
        self.ui.partition_list_widget.clear()
        disk_size = self.ui.disk_size_line_edit.text()
        if (not disk_size) or (not self.selected_arch_list):
            return
        data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for gi in self.view_model.arch:
            fc = gi.get('fonds_code')
            ye = gi.get('year')
            rp = gi.get('retention_period')
            data[fc][ye][rp].append(gi)
            data[fc][rp][ye].append(gi)
        selected_arch_data = []
        for sa in self.selected_arch_list:
            fc, x1, x2 = sa.split('-')
            selected_arch_data.extend(data[fc][x1][x2])
        from pprint import pprint
        pprint(selected_arch_data)
        item = QListWidgetItem(QIcon(self.disk_icon_path), f'disk1({self.selected_arch_list[0]})')
        self.ui.partition_list_widget.addItem(item)
