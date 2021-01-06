# -*- coding: utf-8 -*-
"""
@file: arch_browser.py
@desc: 档案浏览
@author: Jaden Wu
@time: 2020/11/22 21:45
"""
import os
import glob
from collections import defaultdict
import math
import json

from PySide2 import QtWidgets, QtCore, QtGui

from photo_arch.use_cases.interfaces.dataset import GroupOutputData, PhotoOutputData
from photo_arch.infrastructures.user_interface.qt.interaction.utils import static, extend_slot
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting

from photo_arch.infrastructures.databases.db_setting import session
from photo_arch.adapters.controller.arch_browser import Controller, Repo


class View(object):
    def __init__(self, mw_: MainWindow):
        self.ui: Ui_MainWindow = mw_.ui
        self.tv_browse_pre_sel_text = ''
        self.tv_browse_pre_sel_item = None

        self.ui.photo_list_widget.setViewMode(QtWidgets.QListWidget.IconMode)
        self.ui.photo_list_widget.setIconSize(QtCore.QSize(100, 100))
        self.ui.photo_list_widget.setFixedHeight(146)  # 考虑滚动条
        self.ui.photo_list_widget.setWrapping(False)  # 只一行显示
        self.ui.photo_list_widget.setMovement(QtWidgets.QListWidget.Static)

        self.ui.photo_view_in_arch.setAlignment(QtGui.Qt.AlignCenter)

    def display_group(self, group, widget_suffix='_in_group_arch'):
        for k, v in group.items():
            widget_name = k + widget_suffix
            if hasattr(self.ui, widget_name):
                widget = getattr(self.ui, widget_name)
                widget.setText(v)

    def _fill_model_from_dict(self, parent, d):
        if isinstance(d, dict):
            for k, v in d.items():
                child = QtGui.QStandardItem(str(k))
                parent.appendRow(child)
                self._fill_model_from_dict(child, v)
        elif isinstance(d, list):
            for v in d:
                self._fill_model_from_dict(parent, v)
        else:
            item = QtGui.QStandardItem(str(d))
            parent.appendRow(item)
            if self.tv_browse_pre_sel_text == d:
                self.tv_browse_pre_sel_item = item

    def display_browse_arch(self, arch, priority_key='年度'):
        data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for gi in arch:
            fc = gi.get('fonds_code')
            ye = gi.get('year')
            rp = gi.get('retention_period')
            gp = gi.get('group_path')
            group_code, _, group_title = gp.split(' ')
            group_sn = group_code.split('-')[-1]
            group_name = f'{group_sn} {group_title}'
            if priority_key == '年度':
                data[fc][ye][rp].append(group_name)
            else:
                data[fc][rp][ye].append(group_name)
        model = QtGui.QStandardItemModel()
        model.setHorizontalHeaderItem(0, QtGui.QStandardItem("照片档案"))
        self.tv_browse_pre_sel_text = self._get_tv_browse_sel_text()
        self._fill_model_from_dict(model.invisibleRootItem(), data)
        self.ui.arch_tree_view_browse.setModel(model)
        self.ui.arch_tree_view_browse.expandAll()
        if self.tv_browse_pre_sel_item:
            idx = model.indexFromItem(self.tv_browse_pre_sel_item)
            self.ui.arch_tree_view_browse.setCurrentIndex(idx)
        self.tv_browse_pre_sel_item = None

    def _get_tv_browse_sel_text(self):
        group_code = self.ui.group_code_in_group_arch.text()
        group_sn = group_code.split('-')[-1]
        group_title = self.ui.group_title_in_group_arch.text()
        group_name = f'{group_sn} {group_title}'.strip()
        if group_name:
            return group_name
        else:
            return ''

    def display_photo_info(self, photo_info, widget_suffix='_in_photo_arch'):
        for k, v in photo_info.items():
            widget_name = k + widget_suffix
            if hasattr(self.ui, widget_name):
                widget = getattr(self.ui, widget_name)
                widget.setText(v)


class ArchBrowser(object):
    def __init__(self, mw_: MainWindow, setting: Setting):
        self.ui: Ui_MainWindow = mw_.ui
        self.setting = setting
        self.controller = Controller(Repo(session))
        self.view = View(mw_)

        self.pixmap = None
        self.group_folder = ''

        self.ui.photo_list_widget.itemSelectionChanged.connect(static(self.display_photo))
        extend_slot(self.ui.photo_view_in_arch.resizeEvent, static(self.resize_image))
        extend_slot(self.ui.arch_tree_view_browse.selectionChanged, static(self.show_group))
        extend_slot(self.ui.photo_list_widget.focusInEvent, static(self.set_selected))
        self.ui.order_combobox_browse.currentTextChanged.connect(static(self.display_arch))

    def resize_image(self, event):
        if not self.pixmap:
            return
        size = event.size()
        w, h = size.width() - 1, size.height() - 1  # wow
        pixmap = self.pixmap.scaled(
            w,
            h,
            QtGui.Qt.KeepAspectRatio,
            QtGui.Qt.SmoothTransformation
        )
        self.ui.photo_view_in_arch.setPixmap(pixmap)

    def show_group(self, item_selection):
        indexes = item_selection.indexes()
        if not indexes:
            return
        self._clear_data()
        index: QtCore.QModelIndex = indexes[0]
        if index.child(0, 0).data():  # 点击的不是组名则返回
            return
        parent = index.parent()
        p_parent = parent.parent()
        parent_data = parent.data()
        if parent_data.isdigit():
            year, period = parent_data, p_parent.data()
        else:
            year, period = p_parent.data(), parent_data
        group_sn = index.data().split(' ')[0]
        group_arch_code = f'{self.setting.fonds_code}-ZP·{year}-{period}-{group_sn}'
        _, data = self.controller.get_group(group_arch_code)
        self.view.display_group(data)
        self._list_photo_thumb()

    def _clear_data(self):
        for k in GroupOutputData().__dict__:
            widget_name = f'{k}_in_group_arch'
            if hasattr(self.ui, widget_name):
                getattr(self.ui, widget_name).setText('')
        for k in PhotoOutputData().__dict__:
            getattr(self.ui, f'{k}_in_photo_arch').setText('')
        self.ui.photo_list_widget.clear()
        self.ui.photo_view_in_arch.clear()

    def _list_photo_thumb(self):
        self.ui.photo_list_widget.clear()
        year = self.ui.year_in_group_arch.text()
        period = self.ui.retention_period_in_group_arch.text()
        group_code = self.ui.group_code_in_group_arch.text()
        taken_time = self.ui.taken_time_in_group_arch.text()
        group_title = self.ui.group_title_in_group_arch.text()
        self.group_folder = f'{group_code} {taken_time} {group_title}'
        path = os.path.join(
            self.setting.description_path,
            '照片档案',
            year, period,
            self.group_folder,
            'thumbs',
            '*.*'
        )
        for i, fp in enumerate(glob.iglob(path)):
            item = QtWidgets.QListWidgetItem(QtGui.QIcon(fp), os.path.split(fp)[1].split('-')[-1])  # 只显示张序号
            self.ui.photo_list_widget.addItem(item)
            if i in range(3):
                QtWidgets.QApplication.processEvents()  # 前n张一张接一张显示

    def display_photo(self):
        item_list = self.ui.photo_list_widget.selectedItems()
        if item_list:
            item_text = item_list[0].text()  # photo_sn + format
            group_arch_code = self.ui.arch_code_in_group_arch.text()
            photo_name = f'{group_arch_code}-{item_text}'
            self._display_photo_info(photo_name)
            self._display_image(photo_name)

    def _display_photo_info(self, photo_name):
        photo_arch_code, _ = photo_name.split('.')
        _, photo_info = self.controller.get_photo_info(photo_arch_code)
        self.view.display_photo_info(photo_info)

    def _display_image(self, photo_name):
        group_code = self.group_folder.split(' ')[0]
        year, period, _ = group_code.split('·')[1].split('-')
        group_folder_path = os.path.join(
            self.setting.description_path,
            '照片档案',
            year, period,
            self.group_folder
        )
        path = os.path.join(group_folder_path, photo_name)
        if not os.path.exists(path):
            path = os.path.join(group_folder_path, photo_name.split('-')[-1])
        self.pixmap = QtGui.QPixmap()
        self.pixmap.load(path)
        self._mark_face(self.pixmap, photo_name)
        pixmap = self.pixmap.scaled(
            self.ui.photo_view_in_arch.size(),
            QtGui.Qt.KeepAspectRatio,
            QtGui.Qt.SmoothTransformation
        )
        self.ui.photo_view_in_arch.setPixmap(pixmap)

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

    def display_arch(self, priority_key):
        _, arch = self.controller.browse_arch()
        self.view.display_browse_arch(arch, priority_key)

    def set_selected(self):
        selected_items = self.ui.photo_list_widget.selectedItems()
        if (not selected_items) and self.ui.photo_list_widget.count():
            self.ui.photo_list_widget.item(0).setSelected(True)
