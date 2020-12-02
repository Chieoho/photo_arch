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
from distutils.dir_util import copy_tree
import os

from dataclasses import dataclass
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from photo_arch.infrastructures.user_interface.qt.interaction.utils import (
    static, table_widget_to_xls)
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting

from photo_arch.infrastructures.databases.db_setting import engine, make_session
from photo_arch.adapters.controller.arch_transfer import Controller, Repo


@dataclass
class Group:
    fonds_code: str = ''
    arch_category_code: str = ''
    group_code: str = ''
    group_title: str = ''
    taken_time: str = ''
    taken_locations: str = ''
    photographer: str = ''
    photo_num: str = ''


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
        selected_group_list = self._get_selected_group()
        self.partition_list = []
        selected_cond, used_size, group_list = '', 0, []
        for sc_sgl in selected_group_list:
            selected_cond, sgl = sc_sgl
            for gi in sgl:
                folder_size = float(gi['folder_size'])
                used_size += folder_size
                if used_size < cd_size:
                    group_list.append(gi)
                else:
                    used_size -= folder_size
                    partition = {"used_size": used_size, 'group_list': group_list, 'selected_cond': selected_cond}
                    self.partition_list.append(partition)
                    used_size, group_list = 0, []
                    used_size += folder_size
                    group_list.append(gi)
            if used_size:
                partition = {"used_size": used_size, 'group_list': group_list, 'selected_cond': selected_cond}
                self.partition_list.append(partition)

        self._display_partition_res()

    def _get_selected_group(self):
        selected_group_list = []
        for sc in self.selected_condition_list:
            fc, x1, x2 = sc.split('-')
            if x1.isdigit():
                ye, rp = x1, x2
            else:
                rp, ye = x1, x2
            _, archives = self.controller.get_selected_arch(fc, ye, rp)
            selected_group_list.append((sc, archives))
        return selected_group_list

    def _display_partition_res(self):
        for i, p in enumerate(self.partition_list, 1):
            item = QListWidgetItem(QIcon(self.disk_icon_path), f'{p["selected_cond"]} {i}号')
            self.ui.partition_list_widget.addItem(item)

    def display_cd_info(self):
        self._clear_data()
        if not self.selected_condition_list:
            return
        selected_items = self.ui.partition_list_widget.selectedItems()
        if selected_items:
            item = selected_items[0]
            row = self.ui.partition_list_widget.row(item)
            group_list = self.partition_list[row]['group_list']
            self._display_cd_catalog(group_list)
            self._display_cd_caption()
            self._display_cd_label(row)

    def _clear_data(self):
        for i in range(self.ui.cd_catalog_table_widget.rowCount(), -1, -1):
            self.ui.cd_catalog_table_widget.removeRow(i)

        self.ui.cd_group_codes_line_edit.setText('')
        self.ui.cd_photo_num_line_edit.setText('')
        self.ui.cd_num_line_edit.setText('')

    def _display_cd_catalog(self, group_list):
        for row, gi in enumerate(group_list):
            self.ui.cd_catalog_table_widget.insertRow(row)
            for col, key in enumerate(Group().__dict__):
                item_text = gi.get(key, '')
                item = QTableWidgetItem(str(item_text))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.ui.cd_catalog_table_widget.setItem(row, col, item)

    def _display_cd_caption(self):
        operation_date = time.strftime('%Y%m%d')
        self.ui.operation_date_line_edit.setText(operation_date)
        self.ui.operator_line_edit.setText(self.setting.fonds_name)

    def _display_cd_label(self, row):
        self.ui.cd_fonds_name_line_edit.setText(self.setting.fonds_name)
        self.ui.cd_fonds_code_line_edit.setText(self.setting.fonds_code)
        group_list = self.partition_list[row]['group_list']
        if not group_list:
            return
        start_group_code = group_list[0]['group_code']
        end_group_code = group_list[-1]['group_code']
        self.ui.cd_group_codes_line_edit.setText(f'{start_group_code} 至 {end_group_code}')
        total_num = sum(map(lambda g: int(g['photo_num']), group_list))
        self.ui.cd_photo_num_line_edit.setText(str(total_num))
        self.ui.cd_num_line_edit.setText(f'{row+1}号')

    def package(self):
        for r in range(self.ui.partition_list_widget.count()):
            item = self.ui.partition_list_widget.item(r)
            item.setSelected(True)
            cd_name = item.text()
            cd_path = os.path.join(self.setting.package_path, cd_name)
            group_list = self.partition_list[r]['group_list']
            for gi in group_list:
                group_name = gi['group_path']
                src_abspath = os.path.join(
                    self.setting.description_path,
                    '照片档案',
                    gi['year'],
                    gi['retention_period'],
                    group_name)
                dst_abspath = os.path.join(cd_path, group_name)
                copy_tree(src_abspath, dst_abspath)
            self._gen_catalog_file(cd_path)
            self._gen_caption_file(cd_path)
            self._gen_label_file(cd_path)
        self.mw.msg_box('打包成功', 'info')

    def _gen_catalog_file(self, cd_path):
        xls_name = os.path.split(cd_path)[1] + '.xls'
        xls_path = os.path.join(cd_path, xls_name)
        table_widget_to_xls(self.ui.cd_catalog_table_widget, xls_path)

    def _gen_caption_file(self, cd_path):
        caption_text = f"""题名：{self.ui.cd_title_line_edit.text()}；
光盘型号：{self.ui.cd_model_combo_box.currentText()}；
文件类型：{self.ui.cd_type_combo_box.currentText()}；
制作时间：{self.ui.operation_date_line_edit.text()}；
制作人：{self.ui.operator_line_edit.text()}。"""
        with open(os.path.join(cd_path, 'SM.txt'), 'w') as fw:
            fw.write(caption_text)

    def _gen_label_file(self, cd_path):
        label_text = f"""全宗名称：{self.ui.cd_fonds_name_line_edit.text()}
全宗号：{self.ui.cd_fonds_code_line_edit.text()}

          




起止组号：{self.ui.cd_group_codes_line_edit.text()}
张/件数：{self.ui.cd_photo_num_line_edit.text()}张
光盘类型：{self.ui.cd_type_combo_box.currentText()}
盘号：{self.ui.cd_num_line_edit.text()}"""
        with open(os.path.join(cd_path, '标签.txt'), 'w') as fw:
            fw.write(label_text)
