# -*- coding: utf-8 -*-
"""
@file: photo_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/23 9:24
"""
import json

from PySide2 import QtWidgets, QtCore, QtGui

from photo_arch.use_cases.interfaces.dataset import PhotoInDescription
from photo_arch.infrastructures.user_interface.qt.interaction.utils import static
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting


class View(object):
    def __init__(self, mw_: MainWindow):
        self.mw = mw_

    def display_photo(self, photo_path):
        for k in PhotoInDescription().__dict__:
            widget = getattr(self.mw.ui, f'{k}_in_photo')
            widget.setText(self.mw.photo_info_dict.get(photo_path).get(k, ''))


class PhotoDescription(object):
    def __init__(self, mw_: MainWindow, setting: Setting):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.setting = setting
        self.view = View(mw_)

        self.photo_radio_map = {
            'all_photo_radioButton': 1,
            'part_recognition_radioButton': 2,
            'all_recognition_radioButton': 3
        }
        self.dir_radio_map = {
            'select_dir_radioButton': ('本次识别', 1),
            'current_dir_radioButton': ('当前目录', 2)
        }
        self.pix_map = None
        self.tmp_info = {}
        self.add_icon_path = './icon/add.png'
        self.del_icon_path = './icon/cancel.png'
        
        self.current_photo_id = 0
        self.check_state_dict = {}
        
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.Stretch)

        self.ui.all_photo_radioButton.toggled.connect(static(self.all_photo))
        self.ui.part_recognition_radioButton.toggled.connect(static(self.part_recognition))
        self.ui.all_recognition_radioButton.toggled.connect(static(self.all_recognition))
        self.ui.pre_btn.clicked.connect(static(self.pre_photo))
        self.ui.next_btn.clicked.connect(static(self.next_photo))
        self.ui.tableWidget.itemChanged.connect(static(self.table_item_changed))
        self.ui.select_dir_radioButton.toggled.connect(static(self.dir_choose))
        self.ui.current_dir_radioButton.toggled.connect(static(self.dir_choose))

        self.ui.all_photo_radioButton.setEnabled(False)
        self.ui.part_recognition_radioButton.setEnabled(False)
        self.ui.all_recognition_radioButton.setEnabled(False)

        self.ui.photo_view.resizeEvent = static(self.resize_image)
        self.ui.photo_view.setAlignment(QtCore.Qt.AlignCenter)

        self.ui.pre_btn.setStyleSheet(self.mw.button_style_sheet)
        self.ui.next_btn.setStyleSheet(self.mw.button_style_sheet)

        self.ui.verifycheckBox.stateChanged.connect(static(self.checked))

    def resize_image(self, event):
        if not self.pix_map:
            return
        size = event.size()
        w, h = size.width() - 1, size.height() - 1  # wow
        pix_map = self.pix_map.scaled(w, h, QtGui.Qt.KeepAspectRatio,
                                      QtGui.Qt.SmoothTransformation)
        self.ui.photo_view.setPixmap(pix_map)

    def all_photo(self, check_state):
        self.mw.photo_type = 1
        self._photo_choose(check_state)

    def part_recognition(self, check_state):
        self.mw.photo_type = 2
        self._photo_choose(check_state)

    def all_recognition(self, check_state):
        self.mw.photo_type = 3
        self._photo_choose(check_state)

    def _photo_choose(self, check_state):
        if check_state is False:
            return
        self.ui.tabWidget.setCurrentWidget(self.ui.photo_tab)
        photo_info_list = self.mw.interaction.get_photos_info(self.mw.photo_type,
                                                              self.mw.dir_type)
        self.mw.photo_list = list(map(lambda d: d['photo_path'], photo_info_list))
        self.mw.photo_info_dict = {d['photo_path']: d for d in photo_info_list}
        self.tmp_info = {}
        self.current_photo_id = 0
        self._display_recognizable()

    def dir_choose(self, check_state):
        if check_state is False:
            return
        dir_scope, self.mw.dir_type = self.dir_radio_map[self.mw.sender().objectName()]
        self.ui.all_photo_radioButton.setText(f'显示{dir_scope}所有照片(Alt+Q)')
        self.ui.part_recognition_radioButton.setText(f'显示{dir_scope}部分识别照片(Alt+W)')
        self.ui.all_recognition_radioButton.setText(f'显示{dir_scope}全部识别照片(Alt+E)')
        self.ui.all_photo_radioButton.setShortcut('Alt+Q')
        self.ui.part_recognition_radioButton.setShortcut('Alt+W')
        self.ui.all_recognition_radioButton.setShortcut('Alt+E')

    def get_name_info(self):
        name_list = []
        for row in range(self.ui.tableWidget.rowCount() - 1):
            item_0 = self.ui.tableWidget.item(row, 0)
            id_ = item_0.text() if item_0 else ''
            item_1 = self.ui.tableWidget.item(row, 1)
            name = item_1.text() if item_1 else ''
            name_list.append((id_, name))
        return name_list

    def pre_photo(self):
        self.tmp_info[self.mw.photo_list[self.current_photo_id]] = self.get_name_info()
        if self.current_photo_id > 0:
            self.current_photo_id -= 1
            self._display_recognizable()

    def next_photo(self):
        self.tmp_info[self.mw.photo_list[self.current_photo_id]] = self.get_name_info()
        if self.current_photo_id < len(self.mw.photo_list) - 1:
            self.current_photo_id += 1
            self._display_recognizable()

    def _create_button(self, name, ico_path):
        button = QtWidgets.QPushButton(QtGui.QIcon(QtGui.QPixmap(ico_path)), name,
                                       self.ui.tableWidget)
        button.setFlat(True)
        return button

    def add(self):
        row = self.ui.tableWidget.rowCount() - 1
        del_button = self._create_button('删除', self.del_icon_path)
        del_button.clicked.connect(lambda: self.delete(row))
        self.ui.tableWidget.setCellWidget(row, 2, del_button)
        add_button = self._create_button('添加', self.add_icon_path)
        add_button.clicked.connect(static(self.add))
        self.ui.tableWidget.insertRow(row + 1)
        for col in range(2):
            item = QtWidgets.QTableWidgetItem('')
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.ui.tableWidget.setItem(row+1, col, item)
        self.ui.tableWidget.setCellWidget(row+1, 2, add_button)
        self.ui.verifycheckBox.setCheckState(QtGui.Qt.Unchecked)
        self.check_state_dict[self.mw.photo_list[self.current_photo_id]] = QtGui.Qt.Unchecked

    def delete(self, row):
        self.ui.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.tableWidget.removeRow(row)
        for r in range(row, self.ui.tableWidget.rowCount() - 1):
            self.ui.tableWidget.cellWidget(r, 2).clicked.disconnect()
            self._connect(self.ui.tableWidget.cellWidget(r, 2), r)
        self.ui.verifycheckBox.setCheckState(QtGui.Qt.Unchecked)
        self.check_state_dict[self.mw.photo_list[self.current_photo_id]] = QtGui.Qt.Unchecked
        self.ui.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.CurrentChanged)

    def table_item_changed(self):
        self.ui.verifycheckBox.setCheckState(QtGui.Qt.Unchecked)
        self.check_state_dict[self.mw.photo_list[self.current_photo_id]] = QtGui.Qt.Unchecked
        self._display_peoples()

    def _display_peoples(self):
        name_list = self.get_name_info()
        names = ','.join([n[1] for n in name_list if n[1].strip()])
        self.ui.peoples_in_photo.setText(names)

    def _connect(self, button, row):
        button.clicked.connect(lambda: self.delete(row))

    def _display_recognizable(self):
        if not self.mw.photo_list:
            self.ui.photo_view.setText('没有照片可显示')
            return
        photo_path = self.mw.photo_list[self.current_photo_id]
        self.pix_map = QtGui.QPixmap(photo_path)
        faces_data = self.mw.photo_info_dict.get(photo_path).get('faces')
        name_info_list, coordinate_list = self._conversion_data(faces_data)
        tmp_name_info_list = self.tmp_info.get(photo_path)
        self.ui.tableWidget.itemChanged.disconnect()
        if tmp_name_info_list is None:
            self._update_table_widget(name_info_list)
        else:
            self._update_table_widget(tmp_name_info_list)
        self.ui.tableWidget.itemChanged.connect(static(self.table_item_changed))
        self._mark_face(coordinate_list)
        pix_map = self.pix_map.scaled(
            self.ui.photo_view.size(),
            QtGui.Qt.KeepAspectRatio,
            QtGui.Qt.SmoothTransformation
        )
        self.ui.photo_view.setPixmap(pix_map)
        self.ui.photo_index_label.setText('{}/{}'.format(self.current_photo_id + 1,
                                                         len(self.mw.photo_list)))
        self._set_verify_checkbox(photo_path)
        self.view.display_photo(photo_path)
        self._display_peoples()

    @staticmethod
    def _conversion_data(faces_data):
        name_info_list = []
        coordinate_list = []
        face_coordinates_list = json.loads(faces_data)
        for face_info in face_coordinates_list:
            id_ = str(face_info.get('id'))
            name = face_info.get('name')
            name_info_list.append((id_, name))
            coordinate = json.loads(face_info.get('box'))
            x1, y1, x2, y2 = coordinate
            x, y, w, h = x1, y1, (x2 - x1), (y2 - y1)
            coordinate_list.append((id_, (x, y, w, h)))
        return name_info_list, coordinate_list

    def _update_table_widget(self, name_info_list):
        for row in range(self.ui.tableWidget.rowCount(), -1, -1):
            self.ui.tableWidget.removeRow(row)
        row = -1
        for row, (id_, name) in enumerate(name_info_list):
            self.ui.tableWidget.insertRow(row)
            for col, item in enumerate([id_, name]):
                item = QtWidgets.QTableWidgetItem(item)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.ui.tableWidget.setItem(row, col, item)
            del_button = self._create_button('删除', self.del_icon_path)
            self._connect(del_button, row)
            self.ui.tableWidget.setCellWidget(row, 2, del_button)
        self.ui.tableWidget.insertRow(row+1)
        for col in range(2):
            item = QtWidgets.QTableWidgetItem('')
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.ui.tableWidget.setItem(row+1, col, item)
        add_button = self._create_button('添加', self.add_icon_path)
        add_button.clicked.connect(static(self.add))
        self.ui.tableWidget.setCellWidget(row+1, 2, add_button)

    def _set_verify_checkbox(self, photo_path):
        photo_info = self.mw.photo_info_dict.get(photo_path)
        if photo_info:
            verify_state_code = photo_info.get('verify_state', 0)
            if verify_state_code == 1:
                original_verify_state = QtGui.Qt.Checked
            else:
                original_verify_state = QtGui.Qt.Unchecked
        else:
            original_verify_state = QtGui.Qt.Unchecked
        current_check_state = self.check_state_dict.get(photo_path, original_verify_state)
        if current_check_state == QtGui.Qt.Checked:
            self.ui.verifycheckBox.stateChanged.disconnect()
            self.ui.verifycheckBox.setCheckState(QtGui.Qt.Checked)
            self.ui.verifycheckBox.stateChanged.connect(static(self.checked))
        else:
            self.ui.verifycheckBox.setCheckState(QtGui.Qt.Unchecked)

    def _mark_face(self, coordinate_list):
        painter = QtGui.QPainter(self.pix_map)
        for id_, coordinate in coordinate_list:
            x, y, w, h = coordinate
            font = QtGui.QFont()
            font.setPixelSize(h/3)
            painter.setFont(font)
            pen = QtGui.QPen(QtCore.Qt.yellow)
            painter.setPen(pen)
            pos = QtCore.QRect(x, y, w, h)
            painter.drawText(pos, 0, f'{id_}')
            pen = QtGui.QPen(QtCore.Qt.red)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(x, y, w, h)

    def checked(self):
        if self.ui.verifycheckBox.isChecked() and self.mw.photo_list:
            name_list = self.get_name_info()
            photo_path = self.mw.photo_list[self.current_photo_id]
            size = self.ui.photo_view.size()
            checked_info = {
                "path": photo_path,
                "arch_code": self.ui.arch_code_in_photo.text(),
                "faces": self.mw.photo_info_dict.get(photo_path).get('faces'),
                "table_widget": [{'id': i, 'name': n} for i, n in name_list],
                "label_size": (size.width(), size.height())
            }
            self.mw.interaction.checked(checked_info)
            self.check_state_dict[photo_path] = QtGui.Qt.Checked
