# -*- coding: utf-8 -*-
"""
@file: arch_searcher.py
@desc: 档案搜索
@author: Jaden Wu
@time: 2020/12/7 10:30
"""
import os
import glob
import json
import math
import re
from collections import defaultdict

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
        self.ui: Ui_MainWindow = mw_.ui
        self.ui.photo_list_widget_search.setViewMode(QtWidgets.QListWidget.IconMode)
        self.ui.photo_list_widget_search.setIconSize(QtCore.QSize(100, 100))
        self.ui.photo_list_widget_search.setFixedHeight(146)
        self.ui.photo_list_widget_search.setWrapping(False)
        self.ui.photo_list_widget_search.setMovement(QtWidgets.QListWidget.Static)

    def get_search_keys(self):
        title_keys = self.ui.group_title_search.text()
        peoples_keys = self.ui.peoples_search.text()
        year_keys = self.ui.time_search.text()
        return title_keys, peoples_keys, year_keys

    def display_group_list(self, group_arch_code_list, fonds_code):
        self.ui.group_tree_widget_search.clear()
        self.ui.photo_list_widget_search.clear()

        data = defaultdict(lambda: defaultdict(list))
        for group_arch_code in group_arch_code_list:
            year, period, _ = group_arch_code.split('·')[1].split('-')
            data[year][period].append(group_arch_code)

        root = QtWidgets.QTreeWidgetItem(self.ui.group_tree_widget_search)
        root.setText(0, fonds_code)
        root.setFlags(root.flags() | QtGui.Qt.ItemIsTristate | QtGui.Qt.ItemIsUserCheckable)

        for year in data:
            one = QtWidgets.QTreeWidgetItem(root)
            one.setText(0, year)
            one.setFlags(one.flags() | QtGui.Qt.ItemIsTristate | QtGui.Qt.ItemIsUserCheckable)
            for period in data[year]:
                two = QtWidgets.QTreeWidgetItem(one)
                two.setText(0, period)
                two.setFlags(two.flags() | QtGui.Qt.ItemIsTristate | QtGui.Qt.ItemIsUserCheckable)
                for group_arch_code in data[year][period]:
                    three = QtWidgets.QTreeWidgetItem(two)
                    three.setText(0, group_arch_code)
                    three.setCheckState(0, QtGui.Qt.Unchecked)

        self.ui.group_tree_widget_search.expandAll()

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

    def display_photo_list(self, photo_info_list):
        self.ui.group_tree_widget_search.clear()
        self.ui.photo_list_widget_search.clear()
        for i, photo_path in enumerate(photo_info_list):
            head, tail = os.path.split(photo_path)
            photo_sn = tail.split('-')[-1]
            thumb_path = os.path.join(head, 'thumbs', tail)
            if not os.path.exists(thumb_path):
                thumb_path = os.path.join(head, 'thumbs', photo_sn)
            item = QtWidgets.QListWidgetItem(QtGui.QIcon(thumb_path), tail.split('·')[-1])
            self.ui.photo_list_widget_search.addItem(item)
            if i in range(3):
                QtWidgets.QApplication.processEvents()

    def get_path_info(self):
        year = self.ui.year_in_group_search.text()
        period = self.ui.retention_period_in_group_search.text()
        group_code = self.ui.group_code_in_group_search.text()
        taken_time = self.ui.taken_time_in_group_search.text()
        group_title = self.ui.group_title_in_group_search.text()
        return year, period, group_code, taken_time, group_title

    def display_thumbs(self, thumb_paths):
        self.ui.photo_list_widget_search.clear()
        for i, fp in enumerate(thumb_paths):
            item = QtWidgets.QListWidgetItem(QtGui.QIcon(fp), os.path.split(fp)[1].split('-')[-1])  # 只显示张序号
            self.ui.photo_list_widget_search.addItem(item)
            if i in range(3):
                QtWidgets.QApplication.processEvents()  # 前n张一张接一张显示

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
            QtGui.Qt.SmoothTransformation
        )
        self.ui.photo_view_search.setPixmap(scaled_pixmap)


class ArchSearcher(object):
    def __init__(self, mw_: MainWindow, setting: Setting):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.setting = setting
        self.controller = Controller(Repo(session))
        self.view = View(mw_)

        self.pixmap = None

        self.ui.search_btn.clicked.connect(static(self.search))
        self.ui.group_tree_widget_search.itemSelectionChanged.connect(static(self.display_group_info))
        self.ui.photo_list_widget_search.itemSelectionChanged.connect(static(self.display_photo))
        extend_slot(self.ui.photo_view_search.resizeEvent, static(self.resize_image))
        self.ui.export_btn_search.clicked.connect(static(self.expert))

    def search(self):
        title_keys, people_keys, year_keys = map(lambda s: s.strip(), self.view.get_search_keys())
        title_key_list = re.split(r'\s+', title_keys)
        year_key_list = re.split(r'\s+', year_keys)
        if people_keys:
            people_key_list = re.split(r'\s+', people_keys)
            res, photo_info_list = self.controller.search_photos(title_key_list, people_key_list,
                                                                 year_key_list)
            self.view.display_photo_list(photo_info_list)

        else:
            res, group_arch_code_list = self.controller.search_groups(title_key_list, year_key_list)
            self.view.display_group_list(group_arch_code_list, self.setting.fonds_code)
        self.view.clear_group_info()
        self.view.clear_photo_info()

    def display_group_info(self):
        item_list = self.ui.group_tree_widget_search.selectedItems()
        if item_list:
            group_arch_code = item_list[0].text(0)
            _, data = self.controller.get_group(group_arch_code)
            self.view.display_group_info(data)
            self._list_photo_thumb()
        else:
            self.view.clear_group_info()
            self.view.clear_photo_info()

    def _list_photo_thumb(self):
        year, period, group_code, taken_time, group_title = self.view.get_path_info()
        group_folder = f'{group_code} {taken_time} {group_title}'
        path = os.path.join(
            self.setting.description_path,
            '照片档案',
            year, period,
            group_folder,
            'thumbs',
            '*.*'
        )
        self.view.display_thumbs(glob.iglob(path))

    def display_photo(self):
        item_list = self.ui.photo_list_widget_search.selectedItems()
        if item_list:
            item_text = item_list[0].text()
            item_text_slices = item_text.split('-')
            part_group_arch_code = '-'.join(item_text_slices[0: -1])
            photo_sn_and_format = item_text_slices[-1]
            if len(item_text.split('.')[0]) > 4:
                group_arch_code = f'{self.setting.fonds_code}-ZP·{part_group_arch_code}'
                _, data = self.controller.get_group(group_arch_code)
                self.view.display_group_info(data)
                group_arch_code = data['arch_code']
                photo_name = f'{group_arch_code}-{photo_sn_and_format}'
            else:
                group_arch_code = self.ui.arch_code_in_group_search.text()
                photo_name = f'{group_arch_code}-{photo_sn_and_format}'
            self._display_photo_info(photo_name)
            self._display_image(photo_name, photo_sn_and_format)
        else:
            self.view.clear_photo_info()

    def _display_photo_info(self, photo_name):
        photo_arch_code, _ = photo_name.split('.')
        _, photo_info = self.controller.get_photo_info(photo_arch_code)
        self.view.display_photo_info(photo_info)

    def _display_image(self, photo_name, photo_sn):
        year, period, group_code, taken_time, group_title = self.view.get_path_info()
        group_folder = f'{group_code} {taken_time} {group_title}'
        group_folder_path = os.path.join(
            self.setting.description_path,
            '照片档案',
            year, period,
            group_folder
        )
        path = os.path.join(group_folder_path, photo_name)
        if not os.path.exists(path):
            path = os.path.join(group_folder_path, photo_sn)
        self.pixmap = QtGui.QPixmap()
        self.pixmap.load(path)
        self._mark_face(self.pixmap, photo_name)
        self.view.display_image(self.pixmap)

    def _mark_face(self, pixmap, photo_name):
        painter = QtGui.QPainter(pixmap)
        photo_arch_code, _ = photo_name.split('.')
        face_info = self.controller.get_face_info(photo_arch_code)
        face_list = json.loads(face_info['faces'])
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

    def resize_image(self, event: QtGui.QResizeEvent):
        if not self.pixmap:
            return
        pixmap = self.pixmap.scaled(
            event.size(),
            QtGui.Qt.KeepAspectRatio,
            QtGui.Qt.SmoothTransformation
        )
        self.ui.photo_view_search.setPixmap(pixmap)

    def expert(self):
        expert_path = QtWidgets.QFileDialog.getExistingDirectory(
            self.ui.search_archives_tab, "选择文件夹",
            options=QtWidgets.QFileDialog.ShowDirsOnly
        )
        print(expert_path)
