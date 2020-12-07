# -*- coding: utf-8 -*-
"""
@file: arch_browser.py
@desc:
@author: Jaden Wu
@time: 2020/11/22 21:45
"""
import os
import glob
from collections import defaultdict

from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from photo_arch.use_cases.interfaces.dataset import GroupOutputData, PhotoOutputData
from photo_arch.infrastructures.user_interface.qt.interaction.utils import static, extend_slot
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting

from photo_arch.infrastructures.databases.db_setting import engine, make_session
from photo_arch.adapters.controller.arch_browser import Controller, Repo


class View(object):
    def __init__(self, mw_: MainWindow):
        self.mw = mw_

    def display_group(self, group, widget_suffix='_in_group_arch'):
        for k, v in group.items():
            widget_name = k + widget_suffix
            if hasattr(self.mw.ui, widget_name):
                widget = getattr(self.mw.ui, widget_name)
                if isinstance(widget, QComboBox):
                    if v:
                        widget.setCurrentText(v)
                    else:
                        widget.setCurrentIndex(-1)
                else:
                    widget.setText(v)

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

    def display_browse_arch(self, arch, priority_key='年度'):
        data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for gi in arch:
            fc = gi.get('fonds_code')
            ye = gi.get('year')
            rp = gi.get('retention_period')
            gp = gi.get('group_path')
            if priority_key == '年度':
                data[fc][ye][rp].append(gp)
            else:
                data[fc][rp][ye].append(gp)
        model = QStandardItemModel()
        model.setHorizontalHeaderItem(0, QStandardItem("照片档案"))
        self._fill_model_from_dict(model.invisibleRootItem(), data)
        self.mw.ui.arch_tree_view_browse.setModel(model)
        self.mw.ui.arch_tree_view_browse.expandAll()

    def display_photo_info(self, photo_info, widget_suffix='_in_photo_arch'):
        for k, v in photo_info.items():
            widget_name = k + widget_suffix
            if hasattr(self.mw.ui, widget_name):
                widget = getattr(self.mw.ui, widget_name)
                widget.setText(v)


class ArchBrowser(object):
    def __init__(self, mw_: MainWindow, setting: Setting):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.setting = setting
        self.controller = Controller(Repo(make_session(engine)))
        self.view = View(mw_)

        self.pix_map = None
        self.group_folder = ''

        self.ui.photo_list_widget.setViewMode(QListWidget.IconMode)
        self.ui.photo_list_widget.setIconSize(QSize(100, 100))
        self.ui.photo_list_widget.setFixedHeight(118)
        self.ui.photo_list_widget.setWrapping(False)  # 只一行显示
        self.ui.photo_view_in_arch.setAlignment(QtCore.Qt.AlignCenter)

        self.ui.photo_list_widget.itemSelectionChanged.connect(static(self.display_photo))
        extend_slot(self.ui.photo_view_in_arch.resizeEvent, static(self.resize_image))
        extend_slot(self.ui.arch_tree_view_browse.selectionChanged, static(self.show_group))
        self.ui.order_combobox_browse.currentTextChanged.connect(static(self.display_arch))

    def resize_image(self, event):
        if not self.pix_map:
            return
        size = event.size()
        w, h = size.width() - 1, size.height() - 1  # wow
        pix_map = self.pix_map.scaled(
            w,
            h,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.ui.photo_view_in_arch.setPixmap(pix_map)

    def show_group(self, item_selection):
        self._clear_data()
        indexes = item_selection.indexes()
        if not indexes:
            return
        index = indexes[0]
        if index.child(0, 0).data():  # 点击的不是组名则返回
            return
        self.group_folder = index.data()
        group_code = self.group_folder.split(' ')[0]
        _, data = self.controller.get_group(group_code)
        self.view.display_group(data)
        self._list_photo_thumb()

    def _clear_data(self):
        for k in GroupOutputData().__dict__:
            widget_name = f'{k}_in_group_arch'
            if hasattr(self.mw.ui, widget_name):
                getattr(self.mw.ui, widget_name).setText('')
        for k in PhotoOutputData().__dict__:
            getattr(self.mw.ui, f'{k}_in_photo_arch').setText('')
        self.ui.photo_list_widget.clear()
        self.ui.photo_view_in_arch.clear()

    def _list_photo_thumb(self):
        self.ui.photo_list_widget.clear()
        group_code = self.group_folder.split(' ')[0]
        year, period, _ = group_code.split('·')[1].split('-')
        path = os.path.join(
            self.setting.description_path,
            '照片档案',
            year, period,
            self.group_folder,
            '*.*'
        )
        for i, fp in enumerate(glob.iglob(path)):
            item = QListWidgetItem(QIcon(fp), os.path.split(fp)[1])
            self.ui.photo_list_widget.addItem(item)
            if i in range(3):
                QApplication.processEvents()  # 前n张一张接一张显示

    def display_photo(self):
        item_list = self.ui.photo_list_widget.selectedItems()
        if item_list:
            photo_name = item_list[0].text()
            self._display_photo_info(photo_name)
            self._display_image(photo_name)

    def _display_photo_info(self, photo_name):
        photo_arch_code, _ = photo_name.split('.')
        _, photo_info = self.controller.get_photo_info(photo_arch_code)
        self.view.display_photo_info(photo_info)

    def _display_image(self, photo_name):
        group_code = self.group_folder.split(' ')[0]
        year, period, _ = group_code.split('·')[1].split('-')
        path = os.path.join(
            self.setting.description_path,
            '照片档案',
            year, period,
            self.group_folder,
            photo_name
        )
        self.pix_map = QPixmap(path)
        pix_map = self.pix_map.scaled(
            self.ui.photo_view_in_arch.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.ui.photo_view_in_arch.setPixmap(pix_map)

    def display_arch(self, priority_key):
        _, arch = self.controller.browse_arch()
        self.view.display_browse_arch(arch, priority_key)
