# -*- coding: utf-8 -*-
"""
@file: face_searcher.py
@desc:
@author:
@time: 2020/12/7 10:01
"""
import os
import shutil

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
        self.retrieval_path = ''
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
        self.ui.tree_widget_search_face.itemSelectionChanged.connect(static(self.deal_tree_item_selected_changed))
        self.ui.tree_widget_search_face.itemDoubleClicked.connect(static(self.deal_tree_item_double_clicked))
        self.ui.list_widget_search_face.doubleClicked.connect(static(self.deal_double_clicked_list_item))
        self.ui.list_widget_search_face.mousePressEvent = static(self.deal_press_list_widget)

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
        self.ui.retrieve_photo_path.setToolTip(self.file_path)

    def resize_target_image(self, event: QtGui.QResizeEvent):
        if not self.target_pixmap:
            return
        pixmap = self.target_pixmap.scaled(
            event.size(),
            QtGui.Qt.KeepAspectRatio,
            QtGui.Qt.SmoothTransformation
        )
        self.ui.target_view_search_face.setPixmap(pixmap)

    def select_retrieve_dir(self):
        retrieval_path = QtWidgets.QFileDialog.getExistingDirectory(
            self.ui.search_face_tab, "请选择待检索的目录",
            options=QtWidgets.QFileDialog.ShowDirsOnly)
        if not retrieval_path:
            return
        self.retrieval_path = os.path.abspath(retrieval_path)
        self.ui.retieve_dir.setText(self.retrieval_path)
        self.ui.retieve_dir.setToolTip(self.retrieval_path)

    def start_retrieve(self):
        self.ui.result_view_search_face.clear()
        self.ui.list_widget_search_face.clear()
        self.ui.tree_widget_search_face.clear()
        if self.file_path == '':
            self.mw.msg_box('请指定待检索人物的照片.')
        elif self.retrieval_path == '':
            self.mw.msg_box('请选择待检索的目录.')
        else:
            self.mw.overlay(self.ui.result_view_search_face)
            self.ui.retrieve_btn.setEnabled(False)
            self.timer.start(1000)
            ret = self.mw.interaction.start_retrieve(self.file_path, self.retrieval_path)
            if ret == -1:
                self.mw.msg_box('待检索的目录下面没有照片.')

    def _list_photo_thumb(self, retrieve_results_photo_path):
        self.ui.result_view_search_face.clear()
        self.ui.list_widget_search_face.clear()
        for i, fp in enumerate(retrieve_results_photo_path):
            photo_name = os.path.split(fp)[1]
            item = QtWidgets.QListWidgetItem(QtGui.QIcon(fp), f'☐{photo_name}')
            self.ui.list_widget_search_face.addItem(item)
            if i in range(3):
                QtWidgets.QApplication.processEvents()  # 前n张一张接一张显示

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

    def _path_dict_to_tree(self, parent, d):
        for k, v in d.items():
            if isinstance(v, dict):
                child = QtWidgets.QTreeWidgetItem(parent)
                child.setText(0, k)
                child.setToolTip(0, k)
                child.setFlags(child.flags() | QtGui.Qt.ItemIsTristate | QtGui.Qt.ItemIsUserCheckable)
                self._path_dict_to_tree(child, v)
            else:
                child = QtWidgets.QTreeWidgetItem(parent)
                child.setText(0, k)
                child.setToolTip(0, k)
                child.setCheckState(0, QtGui.Qt.Unchecked)

    def _display_photo_tree(self, retrieve_results_photo_path):
        path_dict_ = {}
        path_head, folder = os.path.split(self.retrieval_path)
        for fp in retrieve_results_photo_path:
            _, rp_ = fp.split(path_head)
            rp = rp_[1:] if rp_[0] == os.sep else rp_
            self._attach(path_dict_, rp)
        path_dict = {self.retrieval_path: path_dict_[folder]}
        self.ui.tree_widget_search_face.itemChanged.connect(static(self.deal_tree_item_changed))
        self.ui.tree_widget_search_face.itemChanged.disconnect()
        self.ui.tree_widget_search_face.clear()
        self. _path_dict_to_tree(self.ui.tree_widget_search_face,  path_dict)
        self.ui.tree_widget_search_face.itemChanged.connect(static(self.deal_tree_item_changed))
        self.ui.tree_widget_search_face.expandAll()

    def _display_result(self, retrieve_results_photo_path):
        self._list_photo_thumb(retrieve_results_photo_path)
        self._display_photo_tree(retrieve_results_photo_path)

    def _get_retrieve_result(self):
        self.retrieve_results_photo_path, self.retrieve_results_face_box = \
            self.mw.interaction.get_retrieve_result(self.file_path, self.retrieval_path)
        if len(self.retrieve_results_photo_path) > 0 and len(self.retrieve_results_face_box) > 0:
            self._display_result(self.retrieve_results_photo_path)

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

    @staticmethod
    def _get_tree_item_path(tree_item: QtWidgets.QTreeWidgetItem):
        path = tree_item.text(0)
        parent = tree_item.parent()
        while parent:
            path = f'{parent.text(0)}{os.sep}{path}'
            parent = parent.parent()
        return path

    def deal_tree_item_selected_changed(self):
        item_list = self.ui.tree_widget_search_face.selectedItems()
        if item_list:
            tree_item: QtWidgets.QTreeWidgetItem = item_list[0]
            child = tree_item.child(0)
            if child is None:
                path = self._get_tree_item_path(tree_item)
                row = self.retrieve_results_photo_path.index(path)
                item = self.ui.list_widget_search_face.item(row)
                self.ui.list_widget_search_face.setCurrentItem(item)

    def deal_tree_item_double_clicked(self, tree_item: QtWidgets.QTreeWidgetItem):
        _ = self
        if tree_item.checkState(0) == QtCore.Qt.CheckState.Checked:
            tree_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
        else:
            tree_item.setCheckState(0, QtCore.Qt.CheckState.Checked)

    def deal_tree_item_changed(self, tree_item: QtWidgets.QTreeWidgetItem):
        child = tree_item.child(0)
        if child is None:
            path = self._get_tree_item_path(tree_item)
            row = self.retrieve_results_photo_path.index(path)
            item = self.ui.list_widget_search_face.item(row)
            check_state = tree_item.checkState(0)
            if check_state == QtCore.Qt.CheckState.Checked:
                item.setText(item.text().replace('☐', '☑'))
            else:
                item.setText(item.text().replace('☑', '☐'))

    def _mark_face(self, face_box, pixmap):
        _ = self
        painter = QtGui.QPainter(pixmap)
        x1, y1, x2, y2 = face_box
        x, y, w, h = x1, y1, (x2 - x1), (y2 - y1)
        pen = QtGui.QPen(QtCore.Qt.red)
        pen.setWidth(5)
        painter.setPen(pen)
        painter.drawRect(x, y, w, h)

    def _get_corresponding_child(self, parent: QtWidgets.QTreeWidgetItem, name):
        parts = name.split(os.sep)
        part, name = parts[0], os.sep.join(parts[1:])
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.text(0) == part:
                if child.childCount() == 0:
                    return child
                return self._get_corresponding_child(child, name)

    def display_photo(self):
        item_list = self.ui.list_widget_search_face.selectedItems()
        if not item_list:
            return
        row = self.ui.list_widget_search_face.row(item_list[0])
        face_box = self.retrieve_results_face_box[row]
        self.result_pixmap = QtGui.QPixmap()
        path = self.retrieve_results_photo_path[row]
        root = self.ui.tree_widget_search_face.invisibleRootItem()
        _, relative_path = path.split(self.retrieval_path)
        relative_path = relative_path[1:] if relative_path[0] == os.sep else relative_path
        new_sel_child = self._get_corresponding_child(root.child(0), relative_path)
        self.ui.tree_widget_search_face.itemSelectionChanged.disconnect()
        self.ui.tree_widget_search_face.setCurrentItem(new_sel_child)
        self.ui.tree_widget_search_face.itemSelectionChanged.connect(static(self.deal_tree_item_selected_changed))

        self.result_pixmap.load(path)
        self._mark_face(face_box, self.result_pixmap)
        scaled_pixmap = self.result_pixmap.scaled(
            self.ui.result_view_search_face.size(),
            QtGui.Qt.KeepAspectRatio,
            QtGui.Qt.SmoothTransformation
        )
        self.ui.result_view_search_face.setPixmap(scaled_pixmap)

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

    def _check_thumb(self, row):
        item: QtWidgets.QListWidgetItem = self.ui.list_widget_search_face.item(row)
        root = self.ui.tree_widget_search_face.invisibleRootItem()
        path = self.retrieve_results_photo_path[row]
        _, name = path.split(self.retrieval_path)
        name = name[1:] if name[0] == os.sep else name
        corresponding_child: QtWidgets.QTreeWidgetItem = self._get_corresponding_child(root.child(0), name)
        self.ui.tree_widget_search_face.itemChanged.disconnect()
        if corresponding_child.checkState(0) == QtCore.Qt.CheckState.Checked:
            item.setText(item.text().replace('☑', '☐'))
            corresponding_child.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
        else:
            item.setText(item.text().replace('☐', '☑'))
            corresponding_child.setCheckState(0, QtCore.Qt.CheckState.Checked)
        self.ui.tree_widget_search_face.itemChanged.connect(static(self.deal_tree_item_changed))

    def deal_double_clicked_list_item(self, index: QtCore.QModelIndex):
        row = index.row()
        self._check_thumb(row)

    def deal_press_list_widget(self, e: QtGui.QMouseEvent):
        x, y = e.x(), e.y()
        font_metrics = self.ui.list_widget_search_face.fontMetrics()
        ballot_box_width = font_metrics.width('☐')
        if 106 <= y <= 106 + ballot_box_width:
            lw = self.ui.list_widget_search_face
            row, width, x0 = 0, 0, 0
            for row in range(lw.count()):
                # width = lw.rectForIndex(lw.indexFromItem(lw.item(row))).width()
                width = lw.visualItemRect(lw.item(row)).width()
                if x0 + width > x:
                    break
                x0 += width
            text_width = font_metrics.width(lw.item(row).text())
            d = (width - text_width) / 2
            if (x0 + d) <= x <= (x0 + d + ballot_box_width):
                self._check_thumb(row)
            else:
                QtWidgets.QListWidget.mousePressEvent(self.ui.list_widget_search_face, e)
        else:
            QtWidgets.QListWidget.mousePressEvent(self.ui.list_widget_search_face, e)

    def _get_checked_item(self, parent: QtWidgets.QTreeWidgetItem, checked_item_list):
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.childCount() == 0:
                if child.checkState(0) == QtCore.Qt.CheckState.Checked:
                    checked_item_list.append(child)
            else:
                self._get_checked_item(child, checked_item_list)

    def expert(self):
        root = self.ui.tree_widget_search_face.invisibleRootItem()
        checked_item_list = []
        self._get_checked_item(root, checked_item_list)
        if not checked_item_list:
            self.mw.warn_msg('未勾选照片')
            return
        expert_path = QtWidgets.QFileDialog.getExistingDirectory(
            self.ui.search_archives_tab, "选择文件夹",
            options=QtWidgets.QFileDialog.ShowDirsOnly)
        if expert_path:
            expert_path = os.path.abspath(expert_path)
            selected_paths = map(lambda i: self._get_tree_item_path(i), checked_item_list)
            for sp in selected_paths:
                _, rp = sp.split(self.retrieval_path)
                rp = rp[1:] if rp[0] == os.sep else rp
                dst_path = os.path.join(expert_path, rp)
                dst_path_head, _ = os.path.split(dst_path)
                if not os.path.exists(dst_path_head):
                    os.makedirs(dst_path_head)
                shutil.copy(sp, dst_path)
            self.mw.info_msg('导出成功')
        else:
            self.mw.warn_msg('未选择导出文件夹')
