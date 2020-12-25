# -*- coding: utf-8 -*-
"""
@file: search_faces.py
@desc:
@author:
@time: 2020/12/7 10:01
"""
import os

from PySide2 import QtCore, QtWidgets, QtGui

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
        self.retrieve_results_photo_path = []
        self.retrieve_results_face_box = []
        self.timer = QtCore.QTimer()

        self.ui.searchface_list_widget.setViewMode(QtWidgets.QListWidget.IconMode)
        self.ui.searchface_list_widget.setIconSize(QtCore.QSize(200, 100))
        self.ui.searchface_list_widget.setFixedHeight(146)
        self.ui.searchface_list_widget.setWrapping(False)

        self.ui.searchface_dst_show_view.setAlignment(QtCore.Qt.AlignCenter)

        self.ui.searchface_list_widget.itemSelectionChanged.connect(static(self.display_photo))
        self.ui.searchface_select_photo_btn.clicked.connect(static(self.select_pending_retrieve_photo))
        self.ui.searchface_select_retrieve_dir_btn.clicked.connect(static(self.select_pending_retrieve_dir))
        self.ui.searchface_start.clicked.connect(static(self.start_retrieve))
        self.ui.searchface_retrieve_result_btn.clicked.connect(static(self.get_retrieve_result))
        self.timer.timeout.connect(static(self.get_retrieve_info))

    def select_pending_retrieve_photo(self):
        self.file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.ui.search_face_tab,
            "请选择指定待检索人物的照片", os.getcwd(), "图片(*.*)")
        pix_map = QtGui.QPixmap(self.file_path)
        pix_map = pix_map.scaled(self.ui.searchface_src_view.size(), QtGui.Qt.KeepAspectRatio,
                                 QtGui.Qt.SmoothTransformation)
        self.ui.searchface_src_view.setPixmap(pix_map)
        self.ui.lineEdit.setText(self.file_path)

    def select_pending_retrieve_dir(self):
        self.dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self.ui.search_face_tab, "请选择待检索的目录", os.getcwd())
        self.ui.searchface_retieve_dir_line.setText(self.dir_path)

    def start_retrieve(self):
        self.ui.searchface_dst_show_view.clear()
        self.ui.searchface_list_widget.clear()
        if self.file_path == '':
            self.mw.msg_box('请指定待检索人物的照片.')
        elif self.dir_path == '':
            self.mw.msg_box('请选择待检索的目录.')
        else:
            self.mw.overlay(self.ui.searchface_dst_show_view)
            self.ui.searchface_start.setEnabled(False)
            self.ui.searchface_retrieve_result_btn.setEnabled(False)
            self.timer.start(1000)
            ret = self.mw.interaction.start_retrieve(self.file_path, self.dir_path)
            if ret == -1:
                self.mw.msg_box('待检索的目录下面没有照片.')
            elif ret == -2:
                self.mw.msg_box('内容已被检索过,请点击查看检索结果.')

    def get_retrieve_result(self):
        if self.file_path == '':
            self.mw.msg_box('请指定待检索人物的照片.')
        elif self.dir_path == '':
            self.mw.msg_box('请选择待检索的目录.')
        else:
            self.mw.overlay(self.ui.searchface_dst_show_view)
            self.retrieve_results_photo_path, self.retrieve_results_face_box = \
                self.mw.interaction.get_retrieve_result(self.file_path, self.dir_path)
            if len(self.retrieve_results_photo_path) > 0 and len(self.retrieve_results_face_box) > 0:
                print(self.retrieve_results_photo_path)
                self.list_photo_thumb(self.retrieve_results_photo_path)
            else:
                self.mw.msg_box('未检索到结果,请确认指定的路径是否进行过人脸检索,或者重新开始检索!')

    def display_photo(self):
        item_list = self.ui.searchface_list_widget.selectedItems()
        if not item_list:
            return
        photo_name = item_list[0].text()
        path = os.path.join(self.dir_path, photo_name)
        index = self.retrieve_results_photo_path.index(os.path.abspath(path))
        face_box = self.retrieve_results_face_box[index]
        pix_map = QtGui.QPixmap(path)
        self.mark_face(face_box, pix_map)
        pix_map = pix_map.scaled(
            self.ui.searchface_dst_show_view.size(),
            QtGui.Qt.KeepAspectRatio,
            QtGui.Qt.SmoothTransformation
        )
        self.ui.searchface_dst_show_view.setPixmap(pix_map)

    def list_photo_thumb(self, retrieve_results_photo_path):
        self.ui.searchface_dst_show_view.clear()
        self.ui.searchface_list_widget.clear()
        for i, fp in enumerate(retrieve_results_photo_path):
            item = QtWidgets.QListWidgetItem(QtGui.QIcon(fp), os.path.split(fp)[1])
            self.ui.searchface_list_widget.addItem(item)
            if i in range(3):
                QtWidgets.QApplication.processEvents()  # 前n张一张接一张显示

    def mark_face(self, face_box, pix_map):
        _ = self
        painter = QtGui.QPainter(pix_map)
        x1, y1, x2, y2 = face_box
        x, y, w, h = x1, y1, (x2 - x1), (y2 - y1)
        pen = QtGui.QPen(QtCore.Qt.red)
        pen.setWidth(5)
        painter.setPen(pen)
        painter.drawRect(x, y, w, h)

    def get_retrieve_info(self):
        retrieve_info = self.mw.interaction.get_retrieve_info()
        total_num = retrieve_info.get('total_to_retrieve_photo_num')
        retrieved_num = retrieve_info.get('retrieved_photo_num')
        self.ui.searchface_dst_show_view.setText(f'已检索{retrieved_num}/{total_num}')
        if retrieved_num == total_num:
            self.ui.searchface_start.setEnabled(True)
            self.ui.searchface_retrieve_result_btn.setEnabled(True)
            self.timer.stop()
            self.mw.msg_box('检索完成')
