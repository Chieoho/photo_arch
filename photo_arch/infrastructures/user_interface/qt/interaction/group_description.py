# -*- coding: utf-8 -*-
"""
@file: group_description.py
@desc: 人脸识别
@author: Jaden Wu
@time: 2020/11/23 8:55
"""
import os
import glob
from pathlib import Path
import time
import shutil

from PySide2 import QtWidgets, QtGui

from photo_arch.use_cases.interfaces.dataset import GroupInputData, GroupOutputData, PhotoInDescription
from photo_arch.infrastructures.user_interface.qt.interaction.utils import static, calc_md5, make_thumb
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow, RecognizeState)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting

from photo_arch.infrastructures.databases.db_setting import session
from photo_arch.adapters.controller.group_description import Controller, Repo


class View(object):
    def __init__(self, mw_: MainWindow):
        self.ui: Ui_MainWindow = mw_.ui

    def display_group(self, group, widget_suffix='_in_group'):
        for k, v in group.items():
            widget_name = k + widget_suffix
            if hasattr(self.ui, widget_name):
                widget = getattr(self.ui, widget_name)
                if isinstance(widget, QtWidgets.QComboBox):
                    if v:
                        widget.setCurrentText(v)
                    else:
                        widget.setCurrentIndex(-1)
                else:
                    widget.setText(v)

    def get_group_input(self):
        group_in = GroupInputData()
        for k in group_in.__dict__.keys():
            widget = getattr(self.ui, k+'_in_group')
            if isinstance(widget, QtWidgets.QComboBox):
                value = widget.currentText()
            elif isinstance(widget, QtWidgets.QTextEdit):
                value = widget.toPlainText()
            else:
                value = widget.text()
            setattr(group_in, k, value)
        return group_in


class GroupDescription(object):
    def __init__(self, mw_: MainWindow, setting: Setting):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.setting = setting
        self.controller = Controller(Repo(session))
        self.view = View(mw_)

        self.current_work_path = ''
        self.current_folder = ''
        self.description_path_info = {}
        self.arch_code_info = {}
        self.group_tmp_info = {}

        height = int(self.mw.dt_height*30/1080)
        self.ui.tree_widget_group.setStyleSheet('#tree_widget_group::item{height:%spx;}' % height)
        self.ui.open_dir_btn.clicked.connect(static(self.select_dir))
        self.ui.tree_widget_group.itemDoubleClicked.connect(static(self.tick_item))
        self.ui.tree_widget_group.itemSelectionChanged.connect(static(self.display_group))
        self.ui.add_folder_btn.clicked.connect(static(self.add_folder_item))
        self.ui.cancel_folder_btn.clicked.connect(static(self.cancel_folder_item))
        self.ui.save_group_btn.clicked.connect(static(self.save_and_copy_group))

        self.ui.add_folder_btn.setStyleSheet(self.mw.button_style_sheet)
        self.ui.cancel_folder_btn.setStyleSheet(self.mw.button_style_sheet)
        self.ui.save_group_btn.setStyleSheet(self.mw.button_style_sheet)

        self.clear_group_info()

        self.ui.fonds_code_in_group.textChanged.connect(static(self.update_arch_code))
        self.ui.arch_category_code_in_group.currentTextChanged.connect(static(self.update_group_code))
        self.ui.retention_period_in_group.currentTextChanged.connect(static(self.update_group_code))
        self.ui.year_in_group.textChanged.connect(static(self.update_group_code))
        self.ui.group_title_in_group.textChanged.connect(static(self.update_path))
        self.ui.group_code_in_group.textChanged.connect(static(self.update_path_arch))
        self.ui.taken_time_in_group.textChanged.connect(static(self.update_path_year))

    def clear_group_info(self):
        self.view.display_group(GroupOutputData().__dict__)

    def select_dir(self):
        current_work_path = QtWidgets.QFileDialog.getExistingDirectory(
            self.ui.tree_widget_group, "选择文件夹",
            options=QtWidgets.QFileDialog.ShowDirsOnly)
        if not current_work_path:
            return
        self.ui.tabWidget.setCurrentWidget(self.ui.group_tab)
        self.current_work_path = os.path.abspath(current_work_path)
        self.ui.dir_lineEdit.setText(self.current_work_path)
        self._generate_tree_by_path(self.current_work_path)
        self._reset_state()

    def display_group(self):
        item_list = self.ui.tree_widget_group.selectedItems()
        if not item_list:
            return
        item = item_list[0]
        if item.text(0) == self.current_work_path:
            return
        self._keep_tmp_info(self.current_folder)
        group_folder = item.text(0)
        if group_folder in self.group_tmp_info:
            self.view.display_group(self.group_tmp_info[group_folder])
        else:
            first_photo = self._find_fist_photo(group_folder)
            first_photo_md5 = calc_md5(first_photo)
            _, group = self.controller.get_group(first_photo_md5)
            if first_photo_md5 and group:
                self.view.display_group(group)
                source_path, dst_abspath = self._get_src_dst_path(group_folder)
                self.description_path_info[source_path] = os.path.join(dst_abspath)
                self.arch_code_info[source_path] = self.ui.arch_code_in_group.text()
                self.mw.msg_box('该组已著录过')
            else:
                path = os.path.join(self.current_work_path, group_folder)
                self._display_default(path)
        self.current_folder = group_folder

    def _keep_tmp_info(self, group_folder):
        group_info = self.view.get_group_input()
        if group_info.group_path:
            self.group_tmp_info[group_folder] = group_info.__dict__

    def update_arch_code(self):
        arch_code_parts = self.ui.arch_code_in_group.text().split('-')
        arch_code_parts[0] = self.ui.fonds_code_in_group.text()
        self.ui.arch_code_in_group.setText('-'.join(arch_code_parts))

    def update_group_code(self):
        arch_category = self.ui.arch_category_code_in_group.currentText()
        year = self.ui.year_in_group.text()
        group_sn = self._get_group_sn(year)
        retention_period = self.ui.retention_period_in_group.currentText()
        group_code = f'{arch_category}·{year}-{retention_period}-{group_sn}'
        self.ui.group_code_in_group.setText(group_code)

    def update_path(self):
        group_path = self.ui.group_path_in_group.text()
        if not group_path:
            return
        group_path_parts = group_path.split(' ')
        group_code, taken_time = group_path_parts[0], group_path_parts[1]
        group_title = self.ui.group_title_in_group.text()
        self.ui.group_path_in_group.setText(' '.join([group_code, taken_time, group_title]))

    def update_path_arch(self):
        group_code = self.ui.group_code_in_group.text()
        group_path_parts = self.ui.group_path_in_group.text().split(' ')
        group_path_parts[0] = group_code
        self.ui.group_path_in_group.setText(' '.join(group_path_parts))
        fonds_code = self.ui.arch_code_in_group.text().split('-')[0]
        self.ui.arch_code_in_group.setText('-'.join([fonds_code, group_code]))

    def update_path_year(self):
        taken_time = self.ui.taken_time_in_group.text()
        group_path_parts = self.ui.group_path_in_group.text().split(' ')
        if len(group_path_parts) >= 2:
            group_path_parts[1] = taken_time
            self.ui.group_path_in_group.setText(' '.join(group_path_parts))
        self.ui.year_in_group.setText(taken_time[0: 4])

    def _display_path_arch_group_code(self):
        group_folder, arch_code, group_code = self._get_path_arch_group_code()
        self.ui.group_path_in_group.setText(group_folder)
        self.ui.arch_code_in_group.setText(arch_code)
        self.ui.group_code_in_group.setText(group_code)

    def save_and_copy_group(self):
        is_path_changed = self._save_group_and_remove_folder()
        self._copy_arch_and_gen_thumbs()
        if is_path_changed:
            self.mw.msg_box('保存成功，组路径已变，若已添加请重新添加', msg_type='info')
        else:
            self.mw.msg_box('保存成功', msg_type='info')

    def _save_group_and_remove_folder(self):
        group_arch_code = self.ui.arch_code_in_group.text()
        if not group_arch_code:
            return
        first_photo = self._find_fist_photo()
        first_photo_md5 = calc_md5(first_photo)
        group_data: GroupInputData = self.view.get_group_input()
        group_data.first_photo_md5 = first_photo_md5
        _, group_info = self.controller.get_group(first_photo_md5)
        is_path_changed = False
        if group_info:
            self._remove_old_group(group_info)
            self.controller.update_group(group_data)
            is_path_changed = not (group_info.get('group_path') == group_data.group_path)
        else:
            self.controller.add_group(group_data)
        return is_path_changed

    def _remove_old_group(self, old_group: dict):
        _ = self
        old_folder_name = old_group.get('group_path')
        old_group_path = self._get_group_folder_path(old_folder_name)
        if os.path.exists(old_group_path):
            shutil.rmtree(old_group_path)

    def _get_group_folder_path(self, group_folder_name):
        group_code, _, _ = group_folder_name.split(' ')
        year, retention_period, _ = group_code.split('·')[1].split('-')
        group_folder_path = os.path.join(
            self.setting.description_path,
            '照片档案',
            year, retention_period,
            group_folder_name
        )
        return group_folder_path

    def _copy_arch_and_gen_thumbs(self):
        source_path, dst_abspath = self._get_src_dst_path()
        self.description_path_info[source_path] = os.path.join(dst_abspath)
        self.arch_code_info[source_path] = self.ui.arch_code_in_group.text()
        if os.path.exists(dst_abspath):
            shutil.rmtree(dst_abspath)
        shutil.copytree(source_path, dst_abspath)
        self._gen_thumbs(source_path, dst_abspath)

    def _get_src_dst_path(self, current_folder=None):
        if current_folder:
            source_path = os.path.join(self.current_work_path, current_folder)
        else:
            source_path = os.path.join(self.current_work_path, self.current_folder)
        group_code = self.ui.group_code_in_group.text()
        taken_time = self.ui.taken_time_in_group.text()
        group_title = self.ui.group_title_in_group.text()
        name = ' '.join([group_code, taken_time, group_title])
        dst_abspath = os.path.join(
            self.setting.description_path,
            '照片档案',
            self.ui.year_in_group.text(),
            self.ui.retention_period_in_group.currentText(),
            name)
        return source_path, dst_abspath

    def _gen_thumbs(self, src_path, dst_path):
        _ = self
        thumb_path = os.path.join(dst_path, 'thumbs')
        if not os.path.exists(thumb_path):
            os.mkdir(thumb_path)
        for f in glob.iglob(os.path.join(src_path, '*')):
            name = os.path.split(f)[1]
            make_thumb(f, os.path.join(thumb_path, name))

    def _find_fist_photo(self, group_folder=None):
        if group_folder is None:
            group_folder = self.current_folder
        path = os.path.join(self.current_work_path, group_folder)
        min_c_time = 32472115200  # 2999-01-01
        first_photo = ''
        for f in glob.iglob(os.path.join(path, '*')):
            c_time = os.stat(f).st_ctime
            if c_time < min_c_time:
                min_c_time = c_time
                first_photo = f
        return first_photo

    def tick_item(self, item):
        group_folder = item.text(0)
        if group_folder == self.current_work_path:
            return
        if item.checkState(0) == QtGui.Qt.Unchecked:
            first_photo = self._find_fist_photo(group_folder)
            first_photo_md5 = calc_md5(first_photo)
            _, group = self.controller.get_group(first_photo_md5)
            if group:
                item.setCheckState(0, QtGui.Qt.Checked)
            else:
                self.mw.msg_box('未完成组著录，请先完成')
        else:
            item.setCheckState(0, QtGui.Qt.Unchecked)

    def cancel_folder_item(self):
        item_value = QtWidgets.QTreeWidgetItemIterator(self.ui.tree_widget_group).value()
        if item_value is None:
            return
        child_count = item_value.childCount()
        for i in range(child_count):
            if item_value.child(i).checkState(0) == QtGui.Qt.Checked:
                item_value.child(i).setCheckState(0, QtGui.Qt.Unchecked)

    def add_folder_item(self):
        self.mw.overlay(self.ui.tree_widget_group)
        arch_code_info = {
            "root": {},
            "children": {}
        }
        root_item = self.ui.tree_widget_group.invisibleRootItem().child(0)
        if root_item is None:
            return
        item_iterator = QtWidgets.QTreeWidgetItemIterator(self.ui.tree_widget_group)
        items_value = item_iterator.value()
        for i in range(items_value.childCount()):
            item = items_value.child(i)
            if item.checkState(0) == QtGui.Qt.Checked:
                path = item.text(0)
                group_abspath = os.path.join(self.current_work_path, path)
                dst_abspath = self.description_path_info.get(group_abspath, '')
                arch_code = self.arch_code_info.get(group_abspath, '')
                arch_code_info["children"].update({dst_abspath: arch_code})
        if self.mw.interaction.set_arch_code(arch_code_info):
            self.mw.msg_box('添加成功', 'info')
            self._reset_state()
        else:
            self.mw.msg_box('添加失败')

    def _reset_state(self):
        self.ui.radio_btn_group.setExclusive(False)
        for rb in [self.ui.all_photo_radioButton,
                   self.ui.part_recognition_radioButton,
                   self.ui.all_recognition_radioButton]:
            rb.setEnabled(True)
            rb.setChecked(False)
        self.ui.radio_btn_group.setExclusive(True)

        self.ui.recogni_btn.setEnabled(True)

        for label in self.mw.rcn_info_label_dict.values():
            label.clear()
        self.ui.progressBar.setValue(0)
        for k in PhotoInDescription().__dict__:
            widget = getattr(self.mw.ui, f'{k}_in_photo')
            widget.setText('')
        self.ui.photo_view.clear()
        for row in range(self.ui.tableWidget.rowCount(), -1, -1):
            self.ui.tableWidget.removeRow(row)
        self.ui.photo_index_label.clear()

        self.mw.run_state = RecognizeState.stop
        self.ui.pausecontinue_btn.setText('停止')
        self.ui.run_state_label.setText("停止")

        self.ui.verifycheckBox.setCheckState(QtGui.Qt.CheckState.Unchecked)

    def _generate_dir_tree(self, root_arch_info, file_arch_list):
        root_path, root_arch_code = root_arch_info
        _, volume_name = os.path.split(root_path)
        self.ui.tree_widget_group.setColumnWidth(0, int(520*self.mw.dt_width/1920))  # 设置列宽
        self.ui.tree_widget_group.clear()
        root = QtWidgets.QTreeWidgetItem(self.ui.tree_widget_group)
        root.setText(0, root_path)
        for name, arch_code in file_arch_list:
            child = QtWidgets.QTreeWidgetItem(root)
            child.setText(0, name)
            child.setCheckState(0, QtGui.Qt.Unchecked)
        self.ui.tree_widget_group.expandAll()

    def _generate_tree_by_path(self, root_path):
        file_list = filter(lambda p: os.path.isdir(os.path.join(root_path, p)), os.listdir(root_path))
        root_arch_info = (root_path, '')
        file_arch_list = [(fp, '') for fp in file_list]
        self._generate_dir_tree(root_arch_info, file_arch_list)

    def _generate_tree_by_data(self, arch_code_info):
        root_arch = arch_code_info['root']
        root_arch_info = list(root_arch.items())[0]
        root_path = root_arch_info[0]
        children_arch = {p: '' for p in filter(lambda p: os.path.isdir(os.path.join(root_path, p)),
                                               os.listdir(root_path))}
        children_arch.update({(fp[len(root_path)+1:], an) for fp, an in arch_code_info['children'].items()})
        arch_list = children_arch.items()
        self._generate_dir_tree(root_arch_info, arch_list)

    def _display_default(self, path):
        group_info = self._gen_default_info(path)
        self.view.display_group(group_info)
        self._display_path_arch_group_code()

    def _gen_default_info(self, path):
        group_data = GroupOutputData()
        group_folder = os.path.split(path)[1]
        group_data.fonds_code = self.setting.fonds_code
        group_data.arch_category_code = 'ZP'
        group_data.retention_period = 'D10'
        group_data.security_classification = '公开资料'
        group_data.opening_state = '主动公开'
        group_data.group_title = group_folder
        folder_size, photo_num, file_create_time = self._get_folder_info(path)
        group_data.folder_size = folder_size
        group_data.photo_num = str(photo_num)
        group_data.taken_time = file_create_time
        group_data.year = file_create_time[0: 4]
        return group_data.__dict__

    def _get_path_arch_group_code(self):
        taken_time = self.ui.taken_time_in_group.text()
        group_title = self.ui.group_title_in_group.text()
        fonds_code = self.ui.fonds_code_in_group.text()
        arch_category = self.ui.arch_category_code_in_group.currentText()
        year = self.ui.year_in_group.text()
        retention_period = self.ui.retention_period_in_group.currentText()
        group_sn = self._get_group_sn(year)
        group_code = f'{arch_category}·{year}-{retention_period}-{group_sn}'
        arch_code = f'{fonds_code}-{group_code}'
        group_folder = f'{group_code} {taken_time} {group_title}'
        return group_folder, arch_code, group_code

    @staticmethod
    def _get_folder_info(path):
        directory = Path(path)
        total_size = 0
        photo_num = 0
        f_stat = None
        file_create_time = ''
        for f in directory.glob('**/*'):
            if f.is_file():
                photo_num += 1
                f_stat = f.stat()
                total_size += f_stat.st_size
        if f_stat:
            file_create_time = time.strftime('%Y%m%d', time.localtime(f_stat.st_ctime))
        mb = 1024 * 1024.0
        folder_size = "%.2f" % (total_size / mb)
        return folder_size, photo_num, file_create_time

    def _get_group_sn(self, year):
        _, group_sn = self.controller.get_group_sn(year)
        group_sn = str(group_sn).zfill(4)
        return group_sn
