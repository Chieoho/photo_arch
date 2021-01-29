# -*- coding: utf-8 -*-
"""
@file: arch_searcher.py
@desc: 档案搜索
@author: Jaden Wu
@time: 2020/12/7 10:30
"""
import os
import json
import math
import re
import shutil

from PySide2 import QtWidgets, QtCore, QtGui

from photo_arch.use_cases.interfaces.dataset import GroupOutputData, PhotoOutputData
from photo_arch.infrastructures.user_interface.qt.interaction.utils import static, extend_slot
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting

from photo_arch.infrastructures.databases.db_setting import session
from photo_arch.adapters.controller.arch_searcher import Controller, Repo


class View(object):
    def __init__(self, mw_: MainWindow):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.ui.photo_list_widget_search.setViewMode(QtWidgets.QListWidget.IconMode)
        self.ui.photo_list_widget_search.setIconSize(QtCore.QSize(100, 100))
        self.ui.photo_list_widget_search.setFixedHeight(146)
        self.ui.photo_list_widget_search.setWrapping(False)
        self.ui.photo_list_widget_search.setMovement(QtWidgets.QListWidget.Static)

        self.ui.search_btn.setStyleSheet(self.mw.button_style_sheet)
        self.ui.export_btn_search.setStyleSheet(self.mw.button_style_sheet)
        self.ui.start_date_search.setDate(QtCore.QDate.currentDate().addYears(-10))
        self.ui.end_date_search.setDate(QtCore.QDate.currentDate())

    def get_search_keys(self):
        title_keys = self.ui.group_title_search.text()
        peoples_keys = self.ui.peoples_search.text()
        start_date = self.ui.start_date_search.date()
        end_date = self.ui.end_date_search.date()
        start_date_str = start_date.toString('yyyyMMdd')
        end_date_str = end_date.toString('yyyyMMdd')
        return title_keys, peoples_keys, start_date_str, end_date_str

    def _photo_dict_to_tree(self, parent, d):
        for k, v in d.items():
            if isinstance(v, dict):
                child = QtWidgets.QTreeWidgetItem(parent)
                child.setText(0, k)
                child.setToolTip(0, k)
                child.setFlags(child.flags() | QtGui.Qt.ItemIsTristate | QtGui.Qt.ItemIsUserCheckable)
                self._photo_dict_to_tree(child, v)
            else:
                child = QtWidgets.QTreeWidgetItem(parent)
                child.setText(0, k)
                child.setToolTip(0, k)
                child.setCheckState(0, QtGui.Qt.Unchecked)

    def display_photo_tree(self, photo_dict):
        self.ui.photo_tree_widget_search.clear()
        self._photo_dict_to_tree(self.ui.photo_tree_widget_search,  photo_dict)
        self.ui.photo_tree_widget_search.expandAll()

    def clear_group_info(self, widget_suffix='_in_group_search'):
        for k in GroupOutputData.__dict__:
            widget_name = k + widget_suffix
            if hasattr(self.ui, widget_name):
                widget = getattr(self.ui, widget_name)
                widget.clear()

    def display_group_info(self, group, widget_suffix='_in_group_search'):
        for k, v in group.items():
            widget_name = k + widget_suffix
            if hasattr(self.ui, widget_name):
                widget = getattr(self.ui, widget_name)
                widget.setText(v)

    def display_thumbs(self, thumb_paths):
        self.ui.photo_list_widget_search.clear()
        self.ui.photo_view_search.clear()
        self.clear_photo_info()
        for i, fp in enumerate(thumb_paths):
            root = self.ui.photo_tree_widget_search.invisibleRootItem()
            photo_arch_code = os.path.split(fp)[1].split('.')[0]
            name = photo_arch_code.replace('-ZP·', '-')
            tree_item = self.get_corresponding_child(root, name)
            photo_sn = photo_arch_code[-4:]
            icon = QtGui.QIcon()
            pixmap = QtGui.QPixmap()
            pixmap.load(fp)
            icon.addPixmap(pixmap)
            if tree_item.checkState(0) == QtCore.Qt.CheckState.Checked:
                text = f'√{photo_sn}'
            else:
                text = photo_sn
            item = QtWidgets.QListWidgetItem(icon, text)
            self.ui.photo_list_widget_search.addItem(item)

    def display_photo_info(self, photo_info, widget_suffix='_in_photo_search'):
        for k, v in photo_info.items():
            widget_name = k + widget_suffix
            if hasattr(self.ui, widget_name):
                widget = getattr(self.ui, widget_name)
                widget.setText(v)

    def clear_photo_info(self, widget_suffix='_in_photo_search'):
        for k in PhotoOutputData.__dict__:
            widget_name = k + widget_suffix
            if hasattr(self.ui, widget_name):
                widget = getattr(self.ui, widget_name)
                widget.clear()
        self.ui.photo_view_search.clear()

    def display_image(self, pixmap):
        scaled_pixmap = pixmap.scaled(
            self.ui.photo_view_search.size(),
            QtGui.Qt.KeepAspectRatio,
            QtGui.Qt.SmoothTransformation)
        self.ui.photo_view_search.setPixmap(scaled_pixmap)

    def get_corresponding_child(self, parent: QtWidgets.QTreeWidgetItem, name):
        parts = name.split('-')
        part, name = parts[0], '-'.join(parts[1:])
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.text(0).split(' ')[0] == part:
                if child.childCount() == 0:
                    return child
                return self.get_corresponding_child(child, name)


class ArchSearcher(object):
    def __init__(self, mw_: MainWindow, setting: Setting):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.setting = setting
        self.controller = Controller(Repo(session))
        self.view = View(mw_)

        self.pixmap = None

        self.ui.search_btn.clicked.connect(static(self.search))
        self.ui.photo_tree_widget_search.itemSelectionChanged.connect(static(self.deal_tree_item_selected_changed))
        self.ui.photo_tree_widget_search.itemDoubleClicked.connect(static(self.tick_tree_item))
        self.ui.photo_list_widget_search.itemSelectionChanged.connect(static(self.display_photo))
        extend_slot(self.ui.photo_view_search.resizeEvent, static(self.resize_image))
        self.ui.export_btn_search.clicked.connect(static(self.expert))
        self.ui.photo_list_widget_search.doubleClicked.connect(static(self.check_thumb))

    def _attach(self, trunk, branch):
        parts = branch[0], branch[1:]
        if len(parts[1]) == 1:
            if parts[0] not in trunk:
                trunk[parts[0]] = {parts[1][0]: None}
            else:
                trunk[parts[0]][parts[1][0]] = None
        else:
            node, others = parts
            if node not in trunk:
                trunk[node] = {}
            self._attach(trunk[node], others)

    def _display_photo_tree(self, photo_arch_codes):
        photo_dict = {}
        for ac in photo_arch_codes:
            self._attach(photo_dict, ac)
        self.view.display_photo_tree(photo_dict)

    def search(self):
        title_keys, people_keys, start_date, end_date = map(lambda s: s.strip(), self.view.get_search_keys())
        title_key_list = re.split(r'\s+', title_keys)
        people_key_list = re.split(r'\s+', people_keys)
        res, photo_info_list = self.controller.search_photos(
            title_key_list,
            people_key_list,
            start_date,
            end_date)
        photo_arch_codes = []
        for pa, gt, pe in photo_info_list:
            pa_parts = pa.split('-')
            pa_parts[-2] += f' {gt}'
            if pe:
                pa_parts[-1] += f' {pe}'
            photo_arch_codes.append(pa_parts)
        self.ui.photo_tree_widget_search.itemChanged.connect(static(self.deal_tree_item_changed))
        self.ui.photo_tree_widget_search.itemChanged.disconnect()
        self._display_photo_tree(photo_arch_codes)
        self.ui.photo_tree_widget_search.itemChanged.connect(static(self.deal_tree_item_changed))
        self.view.clear_group_info()
        self.view.clear_photo_info()
        self.ui.photo_list_widget_search.clear()
        if not photo_info_list:
            self.mw.info_msg('未找到符合条件的档案')

    @staticmethod
    def _get_code(item_list):
        code_list = []
        for item in item_list:
            code = item.text(0).split(' ')[0]
            parent = item.parent()
            while parent:
                code = f'{parent.text(0).split(" ")[0]}-{code}'
                parent = parent.parent()
            code_list.append(code)
        return code_list

    def _list_photo_thumb(self, group_item: QtWidgets.QTreeWidgetItem):
        photo_item_list = [group_item.child(i) for i in range(group_item.childCount())]
        photo_code_list = self._get_code(photo_item_list)
        photo_codes = map(lambda ac: re.sub(r'-', '-ZP·', ac, 1), photo_code_list)
        get_path = self.controller.get_photo_path
        photo_thumbs = map(lambda c: re.sub(c, f'thumbs\\{c}', get_path(c)[1]), photo_codes)
        self.view.display_thumbs(photo_thumbs)

    @staticmethod
    def _get_arch_code(item):
        arch_code = ''
        for _ in range(5):
            item_text = item.text(0).split(' ')[0]
            arch_code = f'{item_text}-{arch_code}' if arch_code else f'{item_text}'
            item = item.parent()
            if item is None:
                break
        return arch_code

    def _display_group_info(self, item_list):
        item = item_list[0]
        arch_code = self._get_arch_code(item)
        if arch_code.count('-') == 3:
            group_arch_code = re.sub(r'-', '-ZP·', arch_code, 1)
            _, data = self.controller.get_group(group_arch_code)
            self.view.display_group_info(data)
            self.ui.photo_list_widget_search.itemSelectionChanged.disconnect()
            self._list_photo_thumb(item_list[0])
            self.ui.photo_list_widget_search.itemSelectionChanged.connect(static(self.display_photo))
        elif arch_code.count('-') == 4:
            photo_arch_code = re.sub(r'-', '-ZP·', arch_code, 1)
            group_arch_code = photo_arch_code[0: -5]
            if self.ui.arch_code_in_group_search.text() != group_arch_code:
                _, data = self.controller.get_group(group_arch_code)
                self.view.display_group_info(data)
                self._list_photo_thumb(item_list[0].parent())
            tree_item: QtWidgets.QTreeWidgetItem = item_list[0]
            photo_index = tree_item.parent().indexOfChild(tree_item)
            sel_item = self.ui.photo_list_widget_search.item(photo_index)
            self.ui.photo_list_widget_search.setCurrentItem(sel_item)

    def deal_tree_item_selected_changed(self):
        item_list = self.ui.photo_tree_widget_search.selectedItems()
        if item_list:
            self._display_group_info(item_list)
        else:
            self.view.clear_group_info()
            self.view.clear_photo_info()

    def _display_photo_info(self, photo_arch_code):
        _, photo_info = self.controller.get_photo_info(photo_arch_code)
        self.view.display_photo_info(photo_info)

    def _mark_face(self, pixmap, photo_arch_code):
        painter = QtGui.QPainter(pixmap)
        face_info = self.controller.get_face_info(photo_arch_code)
        faces = face_info.get('faces')
        face_list = json.loads(faces if faces else '[]')
        box_name_list = []
        for face in face_list:
            name = face['name']
            if name:
                box_name_list.append((json.loads(face['box']), name))
        for (x1, y1, x2, y2), name in box_name_list:
            x, y, w, h = x1, y1, (x2 - x1), (y2 - y1)
            font = QtGui.QFont()
            font.setPixelSize(round(0.35 * h))
            painter.setFont(font)
            pen = QtGui.QPen(QtCore.Qt.yellow)
            painter.setPen(pen)
            pos = QtCore.QRect(x, y, w, h)
            painter.drawText(pos, 0, name[0])
            pen = QtGui.QPen(QtCore.Qt.red)
            width = round(0.37 * math.log(h) + 0.024 * h)
            pen.setWidth(width)
            painter.setPen(pen)
            painter.drawRect(x, y, w, h)

    def _display_image(self, photo_arch_code):
        _, photo_path = self.controller.get_photo_path(photo_arch_code)
        self.pixmap = QtGui.QPixmap()
        self.pixmap.load(photo_path)
        self._mark_face(self.pixmap, photo_arch_code)
        self.view.display_image(self.pixmap)

    def display_photo(self):
        item_list = self.ui.photo_list_widget_search.selectedItems()
        if item_list:
            item = item_list[0]
            photo_sn = item.text()[-4:]
            group_arch_code = self.ui.arch_code_in_group_search.text()
            photo_arch_code = f'{group_arch_code}-{photo_sn}'
            self._display_photo_info(photo_arch_code)
            self._display_image(photo_arch_code)

            # 联动选中结果树的对应项
            root = self.ui.photo_tree_widget_search.invisibleRootItem()
            name = photo_arch_code.replace('-ZP·', '-')
            new_sel_child = self.view.get_corresponding_child(root, name)
            self.ui.photo_tree_widget_search.itemSelectionChanged.disconnect()
            self.ui.photo_tree_widget_search.setCurrentItem(new_sel_child)
            self.ui.photo_tree_widget_search.itemSelectionChanged.connect(static(self.deal_tree_item_selected_changed))
        else:
            self.view.clear_photo_info()

    def resize_image(self, event: QtGui.QResizeEvent):
        if not self.pixmap:
            return
        pixmap = self.pixmap.scaled(
            event.size(),
            QtGui.Qt.KeepAspectRatio,
            QtGui.Qt.SmoothTransformation)
        self.ui.photo_view_search.setPixmap(pixmap)

    def _get_checked_item(self, parent: QtWidgets.QTreeWidgetItem, checked_item_list):
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.childCount() == 0:
                if child.checkState(0) == QtCore.Qt.CheckState.Checked:
                    checked_item_list.append(child)
            else:
                self._get_checked_item(child, checked_item_list)

    def expert(self):
        if not self.setting.lic_ctrl_info.enable_export:
            self.mw.warn_msg('目前license不支持导出！')
            return
        root = self.ui.photo_tree_widget_search.invisibleRootItem()
        checked_item_list = []
        self._get_checked_item(root, checked_item_list)
        if not checked_item_list:
            self.mw.warn_msg('未勾选照片')
            return
        expert_path = QtWidgets.QFileDialog.getExistingDirectory(
            self.ui.search_archives_tab, "选择文件夹",
            options=QtWidgets.QFileDialog.ShowDirsOnly)
        if expert_path:
            checked_code_list = self._get_code(checked_item_list)
            checked_codes = map(lambda ac: re.sub(r'-', '-ZP·', ac, 1), checked_code_list)
            for photo_arch_code in checked_codes:
                _, photo_path = self.controller.get_photo_path(photo_arch_code)
                folder = photo_path.split('\\')[-2]
                dst_path = os.path.join(expert_path, folder)
                if not os.path.exists(dst_path):
                    os.makedirs(dst_path)
                shutil.copy(photo_path, dst_path)
            self.mw.info_msg('导出成功')
        else:
            self.mw.warn_msg('未选择导出文件夹')

    def check_thumb(self, index: QtCore.QModelIndex):
        photo_arch_code = self.ui.arch_code_in_photo_search.text()
        root = self.ui.photo_tree_widget_search.invisibleRootItem()
        name = photo_arch_code.replace('-ZP·', '-')
        corresponding_child: QtWidgets.QTreeWidgetItem = self.view.get_corresponding_child(root, name)
        item: QtWidgets.QListWidgetItem = self.ui.photo_list_widget_search.item(index.row())

        self.ui.photo_tree_widget_search.itemChanged.connect(static(self.deal_tree_item_changed))
        self.ui.photo_tree_widget_search.itemChanged.disconnect()
        if corresponding_child.checkState(0) == QtCore.Qt.CheckState.Checked:
            item.setText(item.text()[-4:])
            corresponding_child.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
        else:
            item.setText(f'√{item.text()}')
            corresponding_child.setCheckState(0, QtCore.Qt.CheckState.Checked)
        self.ui.photo_tree_widget_search.itemChanged.connect(static(self.deal_tree_item_changed))

    def deal_tree_item_changed(self, tree_item: QtWidgets.QTreeWidgetItem):
        if tree_item.child(0) is None:
            group_code_in_tree = self._get_arch_code(tree_item)[0: -5]
            group_code_in_line_edit = self.ui.arch_code_in_group_search.text().replace('-ZP·', '-')
            if group_code_in_tree == group_code_in_line_edit:
                photo_index = tree_item.parent().indexOfChild(tree_item)
                item = self.ui.photo_list_widget_search.item(photo_index)
                if item:
                    check_state = tree_item.checkState(0)
                    if check_state == QtCore.Qt.CheckState.Checked:
                        item.setText(f'√{item.text()}')
                    else:
                        item.setText(item.text()[-4:])

    def tick_tree_item(self, tree_item: QtWidgets.QTreeWidgetItem):
        _ = self
        if tree_item.checkState(0) == QtCore.Qt.CheckState.Checked:
            tree_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
        else:
            tree_item.setCheckState(0, QtCore.Qt.CheckState.Checked)
