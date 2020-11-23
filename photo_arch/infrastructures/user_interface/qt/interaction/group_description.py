# -*- coding: utf-8 -*-
"""
@file: group_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/23 8:55
"""
import os
import typing
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from photo_arch.adapters.controller import GroupInputData
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Overlay, View,
    RecognizeState,
    static, catch_exception,
)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting


class GroupDescription(object):
    def __init__(self, mw_: MainWindow, setting: Setting, view: View):
        self.mw = mw_
        self.setting = setting
        self.view = view

        self.current_work_path = ''
        self.line_edit_prefix = '__line_edit__'

        height = int(self.mw.dt_height*30/1080)
        self.mw.ui.treeWidget.setStyleSheet('#treeWidget::item{height:%spx;}' % (height + 5))
        self.mw.ui.open_dir_btn.clicked.connect(static(self.display_dir))
        self.mw.ui.treeWidget.itemClicked.connect(static(self.item_click))
        self.mw.ui.add_folder_btn.clicked.connect(static(self.add_folder_item))
        self.mw.ui.cancel_folder_btn.clicked.connect(static(self.cancel_folder_item))
        self.mw.ui.save_group_btn.clicked.connect(static(self.save_group))

        self.mw.ui.add_folder_btn.setStyleSheet(self.mw.button_style_sheet)
        self.mw.ui.cancel_folder_btn.setStyleSheet(self.mw.button_style_sheet)
        self.mw.ui.save_group_btn.setStyleSheet(self.mw.button_style_sheet)

        self.display_group()

    @catch_exception
    def save_group(self):
        group_in = GroupInputData()
        for k in group_in.__dict__.keys():
            widget = getattr(self.mw.ui, k+'_in_group')
            if isinstance(widget, QComboBox):
                value = widget.currentText()
            elif isinstance(widget, QTextEdit):
                value = widget.toPlainText()
            else:
                value = widget.text()
            setattr(group_in, k, value)
        self.mw.controller.save_group(group_in)

    @catch_exception
    def display_dir(self):
        current_work_path = QFileDialog.getExistingDirectory(
            self.mw.ui.treeWidget, "选择文件夹",
            options=QFileDialog.ShowDirsOnly
        )
        if not current_work_path:
            return
        self.mw.ui.tabWidget.setCurrentIndex(0)
        self.current_work_path = os.path.abspath(current_work_path)
        self.mw.ui.dir_lineEdit.setText(self.current_work_path)
        overlay = Overlay(self.mw.ui.treeWidget, '初始化中', dynamic=True)
        overlay.show()
        while 1:
            if self.mw.interaction != typing.Any:
                break
            else:
                QApplication.processEvents()
        overlay.hide()
        arch_code_info = self.mw.interaction.get_arch_code(self.current_work_path)
        if arch_code_info and arch_code_info.get('root'):
            self._generate_tree_by_data(arch_code_info)
        else:
            self._generate_tree_by_path(self.current_work_path)
        self._reset_state()

    @catch_exception
    def _reset_state(self):
        self.mw.ui.radio_btn_group.setExclusive(False)
        for rb in [self.mw.ui.all_photo_radioButton,
                   self.mw.ui.part_recognition_radioButton,
                   self.mw.ui.all_recognition_radioButton]:
            rb.setEnabled(True)
            rb.setChecked(False)
        self.mw.ui.radio_btn_group.setExclusive(True)

        self.mw.ui.recogni_btn.setEnabled(True)

        for label in self.mw.rcn_info_label_dict.values():
            label.clear()
        self.mw.ui.progressBar.setValue(0)
        self.mw.ui.arch_code_in_photo.clear()
        self.mw.ui.photo_view.clear()
        for row in range(self.mw.ui.tableWidget.rowCount(), -1, -1):
            self.mw.ui.tableWidget.removeRow(row)
        self.mw.ui.photo_index_label.clear()

        self.mw.run_state = RecognizeState.stop
        self.mw.ui.pausecontinue_btn.setText('停止')
        self.mw.ui.run_state_label.setText("停止")

        self.mw.ui.verifycheckBox.setCheckState(False)

    @catch_exception
    def item_click(self, item):
        if item.text(0) == self.current_work_path:
            return
        if item.checkState(0) == Qt.Unchecked:
            item.setCheckState(0, Qt.Checked)
        else:
            item.setCheckState(0, Qt.Unchecked)

    @catch_exception
    def add_folder_item(self):
        arch_code_info = {
            "root": {},
            "children": {}
        }
        root_item = self.mw.ui.treeWidget.invisibleRootItem().child(0)
        if root_item is None:
            return
        item_iterator = QTreeWidgetItemIterator(self.mw.ui.treeWidget)
        items_value = item_iterator.value()
        for i in range(items_value.childCount()):
            item = items_value.child(i)
            if item.checkState(0) == Qt.Checked:
                path = item.text(0)
                line_edit = self.mw.ui.treeWidget.itemWidget(item, 1)
                arch_code = line_edit.text()
                arch_code_info["children"].update({os.path.join(self.current_work_path, path): arch_code})
        self.mw.interaction.set_arch_code(arch_code_info)
        self._reset_state()

    @catch_exception
    def cancel_folder_item(self):
        item_value = QTreeWidgetItemIterator(self.mw.ui.treeWidget).value()
        if item_value is None:
            return
        child_count = item_value.childCount()
        for i in range(child_count):
            if item_value.child(i).checkState(0) == Qt.Checked:
                item_value.child(i).setCheckState(0, Qt.Unchecked)

    @catch_exception
    def _generate_dir_tree(self, root_arch_info, file_arch_list):
        root_path, root_arch_code = root_arch_info
        _, volume_name = os.path.split(root_path)
        self.mw.ui.treeWidget.setColumnWidth(0, int(520*self.mw.dt_width/1920))  # 设置列宽
        self.mw.ui.treeWidget.clear()
        root = QTreeWidgetItem(self.mw.ui.treeWidget)
        root.setText(0, root_path)
        for name, arch_code in file_arch_list:
            child = QTreeWidgetItem(root)
            child.setText(0, name)
            description_btn = self._gen_description_btn()
            self._connect(description_btn, root_path + '\\' + name)
            self.mw.ui.treeWidget.setItemWidget(child, 1, description_btn)
            child.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            child.setCheckState(0, Qt.Checked)
        self.mw.ui.treeWidget.expandAll()

    @catch_exception
    def _gen_description_btn(self):
        description_btn = QtWidgets.QPushButton(
            ' ',
            self.mw.ui.treeWidget
        )
        font = QFont()
        font.setFamily("新宋体")
        font.setPointSize(14)
        description_btn.setFont(font)
        description_btn.setStyleSheet("text-align: left; padding-left: 18px;")
        description_btn.setFlat(True)
        return description_btn

    @catch_exception
    def _connect(self, button, path):
        button.clicked.connect(lambda: self.display_group(path))

    @catch_exception
    def display_group(self, path=''):
        if path:
            group_name = os.path.split(path)[1]
            self.mw.controller.get_group(group_name)
        else:
            group_name = ''
        self.view.display_group_in_description()
        self.mw.ui.group_path_in_group.setText(group_name)

    @catch_exception
    def _generate_tree_by_path(self, root_path):
        file_list = filter(lambda p: os.path.isdir(os.path.join(root_path, p)), os.listdir(root_path))
        root_arch_info = (root_path, '')
        file_arch_list = [(fp, '') for fp in file_list]
        self._generate_dir_tree(root_arch_info, file_arch_list)

    @catch_exception
    def _generate_tree_by_data(self, arch_code_info):
        root_arch = arch_code_info['root']
        root_arch_info = list(root_arch.items())[0]
        root_path = root_arch_info[0]
        children_arch = {p: '' for p in filter(lambda p: os.path.isdir(os.path.join(root_path, p)),
                                               os.listdir(root_path))}
        children_arch.update({(fp[len(root_path)+1:], an) for fp, an in arch_code_info['children'].items()})
        arch_list = children_arch.items()
        self._generate_dir_tree(root_arch_info, arch_list)
