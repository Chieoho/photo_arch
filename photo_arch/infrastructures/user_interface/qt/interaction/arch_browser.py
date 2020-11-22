# -*- coding: utf-8 -*-
"""
@file: arch_browser.py
@desc:
@author: Jaden Wu
@time: 2020/11/22 21:45
"""
import os
import glob
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow,
    static,
    catch_exception,
)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting


class ArchBrowser(object):
    def __init__(self, mw_: MainWindow):
        self.mw = mw_
        self.pix_map = None
        self.group_name = None

        list_widget = self.mw.ui.photo_list_widget
        list_widget.setViewMode(QListWidget.IconMode)
        list_widget.setIconSize(QSize(200, 150))
        # list_widget.setFixedHeight(235)
        list_widget.setWrapping(False)  # 只一行显示
        list_widget.itemClicked.connect(static(self.display_photo))

        self.mw.ui.photo_view_in_arch.resizeEvent = static(self.resize_image)
        self.mw.ui.photo_view_in_arch.setAlignment(QtCore.Qt.AlignCenter)
        self.mw.ui.arch_tree_view_browse.clicked.connect(static(self.show_group))
        self.mw.ui.order_combobox_browse.currentTextChanged.connect(
            static(self.display_arch))
        self.mw.ui.add_list_btn.setStyleSheet(self.mw.button_style_sheet)

    @catch_exception
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
        self.mw.ui.photo_view_in_arch.setPixmap(pix_map)

    @catch_exception
    def show_group(self, index):
        if index.child(0, 0).data():  # 点击的不是组名则返回
            return
        self.group_name = index.data()
        self.mw.controller.get_group(self.group_name)
        self.mw.view.display_group_in_arch_browse()
        self.mw.ui.photo_view_in_arch.clear()
        self._list_photo_thumb()

    @catch_exception
    def _list_photo_thumb(self):
        self.mw.ui.photo_list_widget.clear()
        path = os.path.join(Setting.path, self.group_name, '*.*')
        for fp in glob.iglob(path):
            item = QListWidgetItem(QIcon(fp), os.path.split(fp)[1])
            self.mw.ui.photo_list_widget.addItem(item)
            QApplication.processEvents()

    @catch_exception
    def display_photo(self, item):
        photo_name = item.text()
        path = os.path.join(Setting.path, self.group_name, photo_name)
        self.pix_map = QPixmap(path)
        pix_map = self.pix_map.scaled(
            self.mw.ui.photo_view_in_arch.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.mw.ui.photo_view_in_arch.setPixmap(pix_map)

    @catch_exception
    def display_arch(self, text):
        self.mw.ui.order_combobox_transfer.setCurrentText(text)
        self.mw.view.display_arch(text)
