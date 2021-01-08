# -*- coding: utf-8 -*-
"""
@file: face_searcher.py
@desc:
@author:
@time: 2020/12/7 10:01
"""
import os

from PySide2 import QtCore, QtWidgets, QtGui

from photo_arch.infrastructures.user_interface.qt.interaction.utils import static, extend_slot
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

        self.target_pixmap = None
        self.result_pixmap = None

        self.ui.list_widget_search_face.setViewMode(QtWidgets.QListWidget.IconMode)
        self.ui.list_widget_search_face.setIconSize(QtCore.QSize(200, 100))
        self.ui.list_widget_search_face.setFixedHeight(146)
        self.ui.list_widget_search_face.setWrapping(False)

        self.ui.target_view_search_face.setAlignment(QtCore.Qt.AlignCenter)
        self.ui.result_view_search_face.setAlignment(QtCore.Qt.AlignCenter)

        self.ui.list_widget_search_face.itemSelectionChanged.connect(static(self.display_photo))
        self.ui.open_photo_btn.clicked.connect(static(self.select_retrieve_photo))
        self.ui.select_retrieve_dir_btn.clicked.connect(static(self.select_retrieve_dir))
        self.ui.retrieve_btn.clicked.connect(static(self.start_retrieve))
        self.timer.timeout.connect(static(self.get_retrieve_info))
        extend_slot(self.ui.target_view_search_face.resizeEvent, static(self.resize_target_image))
        extend_slot(self.ui.result_view_search_face.resizeEvent, static(self.resize_result_image))
        self.ui.export_btn_search_face.clicked.connect(static(self.expert))

    def select_retrieve_photo(self):
        self.file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.ui.search_face_tab,
            "请选择指定待检索人物的照片", os.getcwd(), "图片(*.*)")
        self.target_pixmap = QtGui.QPixmap()
        self.target_pixmap.load(self.file_path)
        scaled_pixmap = self.target_pixmap.scaled(
            self.ui.target_view_search_face.size(),
            QtGui.Qt.KeepAspectRatio,
            QtGui.Qt.SmoothTransformation)
        self.ui.target_view_search_face.setPixmap(scaled_pixmap)
        self.ui.retrieve_photo_path.setText(self.file_path)

    def select_retrieve_dir(self):
        self.dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self.ui.search_face_tab, "请选择待检索的目录", os.getcwd())
        self.ui.retieve_dir.setText(self.dir_path)

    def start_retrieve(self):
        self.ui.result_view_search_face.clear()
        self.ui.list_widget_search_face.clear()
        if self.file_path == '':
            self.mw.msg_box('请指定待检索人物的照片.')
        elif self.dir_path == '':
            self.mw.msg_box('请选择待检索的目录.')
        else:
            self.mw.overlay(self.ui.result_view_search_face)
            self.ui.retrieve_btn.setEnabled(False)
            self.timer.start(1000)
            ret = self.mw.interaction.start_retrieve(self.file_path, self.dir_path)
            if ret == -1:
                self.mw.msg_box('待检索的目录下面没有照片.')

    def display_photo(self):
        item_list = self.ui.list_widget_search_face.selectedItems()
        if not item_list:
            return
        photo_name = item_list[0].text()
        path = os.path.join(self.dir_path, photo_name)
        index = self.retrieve_results_photo_path.index(os.path.abspath(path))
        face_box = self.retrieve_results_face_box[index]
        self.result_pixmap = QtGui.QPixmap()
        self.result_pixmap.load(path)
        self.mark_face(face_box, self.result_pixmap)
        scaled_pixmap = self.result_pixmap.scaled(
            self.ui.result_view_search_face.size(),
            QtGui.Qt.KeepAspectRatio,
            QtGui.Qt.SmoothTransformation
        )
        self.ui.result_view_search_face.setPixmap(scaled_pixmap)

    def display_result(self, retrieve_results_photo_path):
        self._list_photo_thumb(retrieve_results_photo_path)
        self._display_photo_tree(retrieve_results_photo_path)

    def _attach(self, trunk, branch):
        parts = branch.split('\\', 1)
        if '\\' not in parts[1]:  # 已到文件层
            if parts[0] not in trunk:
                trunk[parts[0]] = {parts[1]: None}  # 文件夹不存在则创建（字典相当于文件夹）
            else:
                trunk[parts[0]][parts[1]] = None  # 文件夹存在，则放文件
        else:
            node, others = parts
            if node not in trunk:
                trunk[node] = {}
            self._attach(trunk[node], others)

    def _path_dict_to_tree(self, parent, k, v):
        if isinstance(v, dict):
            child = QtWidgets.QTreeWidgetItem(parent)
            child.setText(0, k)
            child.setFlags(child.flags() | QtGui.Qt.ItemIsTristate | QtGui.Qt.ItemIsUserCheckable)
            for k, v in v.items():
                self._path_dict_to_tree(child, k, v)
        else:
            child = QtWidgets.QTreeWidgetItem(parent)
            child.setText(0, k)
            child.setCheckState(0, QtGui.Qt.Unchecked)

    def _display_photo_tree(self, retrieve_results_photo_path):
        path_dict = {}
        for fp in retrieve_results_photo_path:
            self._attach(path_dict, fp)
        root = QtWidgets.QTreeWidgetItem(self.ui.tree_widget_search_face)
        root.setText(0, [*path_dict.keys()][0])
        root.setFlags(root.flags() | QtGui.Qt.ItemIsTristate | QtGui.Qt.ItemIsUserCheckable)
        self._path_dict_to_tree(root, 'k', [*path_dict.values()][0])
        self.ui.tree_widget_search_face.expandAll()

    def _list_photo_thumb(self, retrieve_results_photo_path):
        self.ui.result_view_search_face.clear()
        self.ui.list_widget_search_face.clear()
        for i, fp in enumerate(retrieve_results_photo_path):
            item = QtWidgets.QListWidgetItem(QtGui.QIcon(fp), os.path.split(fp)[1])
            self.ui.list_widget_search_face.addItem(item)
            if i in range(3):
                QtWidgets.QApplication.processEvents()  # 前n张一张接一张显示

    def mark_face(self, face_box, pixmap):
        _ = self
        painter = QtGui.QPainter(pixmap)
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
        self.ui.result_view_search_face.setText(f'已检索{retrieved_num}/{total_num}')
        self._get_retrieve_result()
        if retrieved_num == total_num:
            self.ui.retrieve_btn.setEnabled(True)
            self.timer.stop()
            self.mw.msg_box('检索完成')

    def _get_retrieve_result(self):
        self.retrieve_results_photo_path, self.retrieve_results_face_box = \
            self.mw.interaction.get_retrieve_result(self.file_path, self.dir_path)
        if len(self.retrieve_results_photo_path) > 0 and len(self.retrieve_results_face_box) > 0:
            self.display_result(self.retrieve_results_photo_path)
        else:
            self.mw.msg_box('未检索到结果,请确认指定的路径是否进行过人脸检索,或者重新开始检索!')

    def resize_target_image(self, event: QtGui.QResizeEvent):
        if not self.target_pixmap:
            return
        pixmap = self.target_pixmap.scaled(
            event.size(),
            QtGui.Qt.KeepAspectRatio,
            QtGui.Qt.SmoothTransformation
        )
        self.ui.target_view_search_face.setPixmap(pixmap)

    def resize_result_image(self, event):
        if not self.result_pixmap:
            return
        size = event.size()
        w, h = size.width() - 1, size.height() - 1
        pixmap = self.result_pixmap.scaled(
            w,
            h,
            QtGui.Qt.KeepAspectRatio,
            QtGui.Qt.SmoothTransformation
        )
        self.ui.result_view_search_face.setPixmap(pixmap)

    def expert(self):
        expert_path = QtWidgets.QFileDialog.getExistingDirectory(
            self.ui.search_face_tab, "选择文件夹",
            options=QtWidgets.QFileDialog.ShowDirsOnly)
        print(expert_path)
