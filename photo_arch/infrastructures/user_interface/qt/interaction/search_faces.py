# -*- coding: utf-8 -*-
"""
@file: search_faces.py
@desc:
@author:
@time: 2020/12/7 10:01
"""
import os

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from photo_arch.infrastructures.user_interface.qt.interaction.utils import static
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting



class SearchFaces(object):
    def __init__(self, mw_: MainWindow, setting: Setting):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.setting = setting

        self.file_path = ''
        self.dir_path = ''
        self.retrive_results_photo_path = []
        self.retrive_results_face_box = []

        self.ui.searchface_list_widget.setViewMode(QListWidget.IconMode)
        self.ui.searchface_list_widget.setIconSize(QSize(100, 100))
        self.ui.searchface_list_widget.setFixedHeight(118)
        self.ui.searchface_list_widget.setWrapping(False)  # 只一行显示
        self.ui.searchface_dst_show_view.setAlignment(QtCore.Qt.AlignCenter)

        self.ui.searchface_list_widget.itemSelectionChanged.connect(static(self.display_photo))

        self.ui.searchface_select_photo_btn.clicked.connect(static(self.select_pending_retrieve_photo))  # 槽函数前要加static函数
        self.ui.searchface_select_retrieve_dir_btn.clicked.connect(static(self.select_pending_retrieve_dir))
        self.ui.searchface_start.clicked.connect(static(self.start_retrieve))
        self.ui.searchface_retrieve_result_btn.clicked.connect(static(self.get_retrieve_result))


    def select_pending_retrieve_photo(self):
        self.file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self.ui.search_face_tab, "请选择指定待检索人物的照片", os.getcwd(), "图片(*.jpg)")
        pix_map = QPixmap(self.file_path)
        pix_map = pix_map.scaled(self.ui.searchface_src_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.ui.searchface_src_view.setPixmap(pix_map)

    def select_pending_retrieve_dir(self):
        self.dir_path = QtWidgets.QFileDialog.getExistingDirectory(self.ui.search_face_tab, "请选择待检索的目录", os.getcwd())
        self.ui.searchface_retieve_dir_line.setText(self.dir_path)


    def start_retrieve(self):
        if self.file_path == '':
            self.mw.msg_box('请指定待检索人物的照片.')
        elif self.dir_path == '':
            self.mw.msg_box('请选择待检索的目录.')
        else:
            ret = self.mw.interaction.start_retrieve(self.file_path, self.dir_path)
            if ret == -1:
                self.mw.msg_box('待检索的目录下面没有照片.')
            elif ret == -2:
                self.mw.msg_box('该目录已检索,请点击查看检索结果.')


    def get_retrieve_result(self):
        self.retrive_results_photo_path, self.retrive_results_face_box = self.mw.interaction.get_retrieve_result(self.file_path, self.dir_path)
        print(self.retrive_results_photo_path)
        self.list_photo_thumb(self.retrive_results_photo_path)


    def display_photo(self):
        item_list = self.ui.searchface_list_widget.selectedItems()
        photo_name = item_list[0].text()
        path = os.path.join(self.dir_path, photo_name)
        index = self.retrive_results_photo_path.index(os.path.abspath(path))
        face_box = self.retrive_results_face_box[index]
        pix_map = QPixmap(path)
        self.mark_face(face_box, pix_map)
        pix_map = pix_map.scaled(
            self.ui.searchface_dst_show_view.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.ui.searchface_dst_show_view.setPixmap(pix_map)


    def list_photo_thumb(self, retrive_results_photo_path):
        self.ui.searchface_list_widget.clear()
        for i, fp in enumerate(retrive_results_photo_path):
            item = QListWidgetItem(QIcon(fp), os.path.split(fp)[1])
            self.ui.searchface_list_widget.addItem(item)
            if i in range(3):
                QApplication.processEvents()  # 前n张一张接一张显示


    def mark_face(self, face_box, pix_map):
        painter = QPainter(pix_map)
        x1, y1, x2, y2 = face_box
        x, y, w, h = x1, y1, (x2 - x1), (y2 - y1)
        # font = QFont()
        # font.setPixelSize(h/3)
        # painter.setFont(font)
        # pen = QPen(QtCore.Qt.yellow)
        # painter.setPen(pen)
        # pos = QRect(x, y, w, h)
        # painter.drawText(pos, 0, f'{id_}')
        pen = QPen(QtCore.Qt.red)
        pen.setWidth(5)
        painter.setPen(pen)
        painter.drawRect(x, y, w, h)