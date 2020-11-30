# -*- coding: utf-8 -*-
"""
@file: arch_transfer.py
@desc:
@author: Jaden Wu
@time: 2020/11/22 21:36
"""
from collections import defaultdict
import time
from typing import List

from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from photo_arch.infrastructures.user_interface.qt.interaction.utils import static
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting

from photo_arch.infrastructures.databases.db_setting import engine, make_session
from photo_arch.adapters.controller.arch_transfer import Controller, Repo


class View(object):
    def __init__(self, mw_: MainWindow):
        self.mw = mw_

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

    def display_transfer_arch(self, arch, priority_key='年度'):
        data = defaultdict(lambda: defaultdict(dict))
        for gi in arch:
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
        self.controller = Controller(Repo(make_session(engine)))
        self.view = View(mw_)

        self.disk_icon_path = './icon/arch_cd.png'
        self.selected_condition_list = []
        self.partition_list: List[dict] = []

        self.ui.partition_list_widget.setViewMode(QListWidget.IconMode)
        self.ui.partition_list_widget.setIconSize(QSize(200, 150))
        self.ui.photo_list_widget.setWrapping(False)  # 只一行显示

        self.ui.order_combobox_transfer.currentTextChanged.connect(static(self.display_arch))
        self.ui.arch_tree_view_transfer.doubleClicked.connect(static(self.select_arch))
        self.ui.selected_arch_list_widget.itemDoubleClicked.connect(static(self.unselect_arch))
        self.ui.cd_size_line_edit.returnPressed.connect(static(self.partition))
        self.ui.across_year_combo_box.currentTextChanged.connect(static(self.partition))
        self.ui.across_period_combo_box.currentTextChanged.connect(static(self.partition))
        self.ui.partition_list_widget.itemSelectionChanged.connect(static(self.display_cd_info))
        self.ui.packeage_btn.clicked.connect(static(self.package))

        catalog_tw = self.ui.cd_catalog_table_widget
        catalog_tw.verticalHeader().setVisible(True)
        catalog_tw.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        catalog_tw.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

    def display_arch(self, priority_key):
        _, arch = self.controller.list_arch()
        self.view.display_transfer_arch(arch, priority_key)

    def select_arch(self, index):
        if index.child(0, 0).data():  # 点击的不是叶子则返回
            return
        parent_index = index.parent()
        fonds_code_index = parent_index.parent()
        selected_name1 = '-'.join([fonds_code_index.data(), parent_index.data(), index.data()])
        selected_name2 = '-'.join([fonds_code_index.data(), index.data(), parent_index.data()])
        if (selected_name1 in self.selected_condition_list) or \
                (selected_name2 in self.selected_condition_list):
            return
        item = QListWidgetItem(selected_name1)
        self.ui.selected_arch_list_widget.addItem(item)
        self.selected_condition_list.append(selected_name1)
        self.partition()

    def unselect_arch(self, item):
        row = self.ui.selected_arch_list_widget.row(item)
        self.ui.selected_arch_list_widget.takeItem(row)
        item_text = item.text()
        if item_text in self.selected_condition_list:
            self.selected_condition_list.remove(item_text)
        self.partition()

    def partition(self):
        self.ui.partition_list_widget.clear()
        cd_size = float(self.ui.cd_size_line_edit.text()) * 1024
        if (not cd_size) or (not self.selected_condition_list):
            return
        selected_arch_list = self._get_selected_arch()

        self.partition_list = []
        used_size, arch_list = 0, []
        for gi in selected_arch_list:
            folder_size = float(gi['folder_size'])
            used_size += folder_size
            if used_size < cd_size:
                arch_list.append(gi)
            else:
                used_size -= folder_size
                self.partition_list.append({"used_size": used_size, 'arch_list': arch_list})
                used_size, arch_list = 0, []
                used_size += folder_size
                arch_list.append(gi)
        if used_size:
            self.partition_list.append({"used_size": used_size, 'arch_list': arch_list})

        self._display_partition_res()

    def _get_selected_arch(self):
        selected_arch_list = []
        for sa in self.selected_condition_list:
            fc, x1, x2 = sa.split('-')
            if x1.isdigit():
                ye, rp = x1, x2
            else:
                rp, ye = x1, x2
            _, arch = self.controller.get_selected_arch(fc, ye, rp)
            selected_arch_list.extend(arch)
        return selected_arch_list

    def _display_partition_res(self):
        for i, sc in enumerate(self.partition_list, 1):
            item = QListWidgetItem(QIcon(self.disk_icon_path), f'{i}号')
            self.ui.partition_list_widget.addItem(item)

    def display_cd_info(self):
        if not self.selected_condition_list:
            return
        row = self.ui.partition_list_widget.currentRow()
        arch_list = self.partition_list[row]['arch_list']
        self._display_cd_catalog(arch_list)
        self._display_cd_caption()
        self._display_cd_label(row)

    def _display_cd_catalog(self, arch_list):
        column_count = self.ui.cd_catalog_table_widget.columnCount()
        key_list = ['fonds_code', 'arch_category_code', 'group_code', 'group_title',
                    'taken_time', 'taken_locations', 'photographer', 'photo_num']
        for i in range(self.ui.cd_catalog_table_widget.rowCount(), -1, -1):
            self.ui.cd_catalog_table_widget.removeRow(i)
        for row, gi in enumerate(arch_list):
            self.ui.cd_catalog_table_widget.insertRow(row)
            for key, col in zip(key_list, range(column_count)):
                item_text = gi.get(key, '')
                item = QTableWidgetItem(str(item_text))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.ui.cd_catalog_table_widget.setItem(row, col, item)

    def _display_cd_caption(self):
        operation_date = time.strftime('%Y%m%d')
        self.ui.operation_date_line_edit.setText(operation_date)

    def _display_cd_label(self, row):
        self.ui.cd_fonds_name_line_edit.setText(self.setting.fonds_name)
        self.ui.cd_fonds_code_line_edit.setText(self.setting.fonds_code)
        arch_list = self.partition_list[row]['arch_list']
        start_group_code = arch_list[0]['group_code']
        end_group_code = arch_list[-1]['group_code']
        self.ui.cd_group_codes_line_edit.setText(f'{start_group_code} 至 {end_group_code}')
        total_num = sum(map(lambda g: int(g['photo_num']), arch_list))
        self.ui.cd_photo_num_line_edit.setText(str(total_num))
        self.ui.cd_num_line_edit.setText(f'{row+1}号')

    def package(self):
        _ = self
        print('打包')
