# -*- coding: utf-8 -*-
"""
@file: qt_gui.py
@desc:
@author: Jaden Wu
@time: 2020/8/20 11:14
"""
import os
import sys
import json
import inspect
import time
from threading import Thread
import typing
from collections import defaultdict
import glob
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from photo_arch.adapters.controller import Controller, GroupInputData
from photo_arch.adapters.sql.repo import Repo
from photo_arch.adapters.presenter import Presenter, ViewModel
from photo_arch.infrastructures.databases.db_setting import engine, make_session
from photo_arch.infrastructures.gui.qt.qt_ui import Ui_MainWindow
from photo_arch.infrastructures.gui.ui_interface import UiInterface


class RunState(object):
    stop = 0
    running = 1
    pause = 2


def catch_exception(func):
    def wrapper(*args):
        try:
            sign = inspect.signature(func)
            return func(*args[0: len(sign.parameters)])
        except Exception as e:
            _ = e
            import traceback
            print(traceback.format_exc())
    return wrapper


class InitRecognition(Thread):
    def __init__(self, mw_instance):
        self.mw_instance = mw_instance
        super().__init__()

    def run(self) -> None:
        if (len(sys.argv) > 1) and (sys.argv[1] in ('-t', '--test')):
            from photo_arch.infrastructures.gui.qt.qt_interaction import QtInteraction
        else:
            from recognition.qt_interaction import QtInteraction
        self.mw_instance.interaction = QtInteraction()


class Overlay(QtWidgets.QWidget):
    def __init__(self, parent, text, dynamic=True, max_dot_num=3):
        QtWidgets.QWidget.__init__(self, parent)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.resize(parent.size())
        if dynamic:
            self.ori_text = text
            self.text = text + ' ' * max_dot_num
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.change_text)
            self.timer.start(1000)
        else:
            self.text = text
        self.counter = 0
        self.max_dot_num = max_dot_num

    def change_text(self):
        self.counter += 1
        if self.counter > self.max_dot_num:
            self.counter = 0
        self.text = self.ori_text + '.' * self.counter + ' ' * (self.max_dot_num - self.counter)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(QFont('新宋体', 15))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text)


view_model = ViewModel()


def get_controller():
    repo = Repo(make_session(engine))
    presenter = Presenter(view_model)
    controller = Controller(repo, presenter)
    return controller


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.interaction: UiInterface = typing.Any
        self.controller = get_controller()
        self.view = View()
        self.init_recognition = InitRecognition(self)
        self.init_recognition.start()

        self.photo_list = []
        self.current_photo_id = 0
        self.photo_info_dict = {}
        self.check_state_dict = {}

        self.rcn_info_label_dict = {
            "recognition_rate": self.ui.recognition_rate_label,
            "recognized_face_num": self.ui.recognized_face_label,
            "part_recognized_photo_num": self.ui.part_recognized_photo_label,
            "all_recognized_photo_num": self.ui.all_recognized_photo_label,
            "handled_photo_num": self.ui.handled_photo_label,
            "unhandled_photo_num": self.ui.unhandled_photo_label
        }
        self.run_state = RunState.stop
        self.ui.tabWidget.currentChanged.connect(self.tab_change)
        self.ui.tabWidget.setCurrentIndex(2)
        self.ui.tabWidget.setCurrentIndex(0)

        desktop = app.desktop()
        self.dt_width, self.dt_height = desktop.width(), desktop.height()
        self.button_style_sheet = "padding-left: {0}px;" \
                                  "padding-right:{0}px;" \
                                  "padding-top:8px; " \
                                  "padding-bottom: 8px;".format(int(30*self.dt_width/1920))

    @catch_exception
    def tab_change(self, tab_id):
        if tab_id == 3:  # 选中“模型训练”tab
            if self.interaction != typing.Any:
                untrained_photo_num = self.interaction.get_untrained_photo_num()
                self.ui.untrained_num_label.setText(str(untrained_photo_num))
        elif tab_id in (4, 5):  # 选中“档案浏览”或“档案移交”tab
            self.controller.browse_arch()
            self.view.display_arch()
        else:
            pass

    @catch_exception
    def msg_box(self, msg: str):
        QMessageBox().warning(self.ui.centralwidget, '提示', msg, QMessageBox.Ok, QMessageBox.Ok)

    @staticmethod
    @catch_exception
    def get_name_info():
        name_list = []
        for row in range(mw.ui.tableWidget.rowCount() - 1):
            item_0 = mw.ui.tableWidget.item(row, 0)
            id_ = item_0.text() if item_0 else ''
            item_1 = mw.ui.tableWidget.item(row, 1)
            name = item_1.text() if item_1 else ''
            name_list.append((id_, name))
        return name_list


mw: MainWindow = typing.Any


class View(object):
    def __init__(self):
        self.view_model = view_model

    def _display_group(self, widget_suffix):
        for k, v in self.view_model.group.items():
            widget_name = k + widget_suffix
            if hasattr(mw.ui, widget_name):
                widget = getattr(mw.ui, widget_name)
                if isinstance(widget, QComboBox):
                    if v:
                        widget.setCurrentText(v)
                    else:
                        widget.setCurrentIndex(-1)
                else:
                    widget.setText(v)

    def display_group_in_description(self):
        self._display_group('_in_group')

    def display_group_in_arch_browse(self):
        self._display_group('_in_group_arch')

    @staticmethod
    def display_photo(photo_path):
        model_keys = [
            'arch_code',
            'photo_code',
            'peoples',
            'format',
            'fonds_code',
            'arch_category_code',
            'year',
            'group_code',
            'photographer',
            'taken_time',
            'taken_locations',
            'security_classification',
            'reference_code'
        ]
        for k in model_keys:
            widget = getattr(mw.ui, f'{k}_in_photo')
            widget.setText(mw.photo_info_dict.get(photo_path).get(k, ''))

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

    def display_arch(self, priority_key='年度'):
        data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for gi in self.view_model.arch:
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
        mw.ui.arch_tree_view_browse.setModel(model)
        mw.ui.arch_tree_view_browse.expandAll()
        mw.ui.arch_tree_view_transfer.setModel(model)
        mw.ui.arch_tree_view_transfer.expandAll()


class Recognition(object):
    update_timer = QtCore.QTimer()

    def __init__(self):
        mw.ui.recogni_btn.clicked.connect(self.run)
        mw.ui.pausecontinue_btn.clicked.connect(self.pause_or_continue)
        Recognition.update_timer.timeout.connect(self.periodic_update)
        Recognition.update_timer.start(1000)
        mw.ui.recogni_btn.setEnabled(False)
        mw.ui.recogni_btn.setStyleSheet(mw.button_style_sheet)
        mw.ui.pausecontinue_btn.setStyleSheet(mw.button_style_sheet)

    @staticmethod
    @catch_exception
    def run():
        if mw.run_state != RunState.running:
            thresh = mw.ui.thresh_lineEdit.text()
            size = mw.ui.photo_view.size()
            params = {
                "threshold": float(thresh) if thresh else 0.9,
                "label_size": (size.width(), size.height())
            }
            result = mw.interaction.start(params)
            if result.get('res') is True:
                mw.run_state = RunState.running
                mw.ui.pausecontinue_btn.setText('停止')
                mw.ui.run_state_label.setText('识别中...')
            else:
                mw.msg_box(result.get('msg'))

    @staticmethod
    @catch_exception
    def pause_or_continue():
        if mw.run_state == RunState.running:
            result = mw.interaction.pause()
            if result.get('res'):
                mw.run_state = RunState.pause
                mw.ui.pausecontinue_btn.setText('继续')
                mw.ui.run_state_label.setText("暂停")
            else:
                mw.msg_box(result.get('msg'))

        elif mw.run_state == RunState.pause:
            result = mw.interaction.continue_run()
            if result.get('res'):
                mw.run_state = RunState.running
                mw.ui.pausecontinue_btn.setText('停止')
                mw.ui.run_state_label.setText('识别中...')
            else:
                mw.msg_box(result.get('msg'))
        else:
            pass

    @staticmethod
    @catch_exception
    def periodic_update():
        if mw.run_state == RunState.running:
            if mw.ui.tabWidget.currentIndex() == 1:
                recognition_info = mw.interaction.get_recognition_info()
                for key, value in recognition_info.items():
                    label = mw.rcn_info_label_dict.get(key)
                    if label:
                        label.setText(str(value))
                handled_photo_num = recognition_info.get('handled_photo_num', 0)
                unhandled_photo_num = recognition_info.get('unhandled_photo_num', 1)
                step = int(handled_photo_num / (handled_photo_num + unhandled_photo_num) * 100)
                mw.ui.progressBar.setValue(step)
                if step >= 100:
                    mw.run_state = RunState.stop
                    mw.ui.pausecontinue_btn.setText('停止')
                    mw.ui.run_state_label.setText("完成")
                    time.sleep(1)
                    photo_info_list = mw.interaction.get_photos_info(PhotoDescription.photo_type,
                                                                     PhotoDescription.dir_type)
                    mw.photo_list = list(map(lambda d: d['photo_path'], photo_info_list))
                    mw.photo_info_dict = {d['photo_path']: d for d in photo_info_list}


class PhotoDescription(object):
    photo_radio_map = {
        'all_photo_radioButton': 1,
        'part_recognition_radioButton': 2,
        'all_recognition_radioButton': 3
    }
    dir_radio_map = {
        'select_dir_radioButton': ('本次识别', 1),
        'current_dir_radioButton': ('当前目录', 2)
    }
    pix_map = None
    tmp_info = {}
    add_icon_path = 'icon/add.png'
    del_icon_path = 'icon/cancel.png'
    photo_type = 1
    dir_type = 1

    def __init__(self):
        mw.ui.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        mw.ui.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        mw.ui.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        mw.ui.all_photo_radioButton.toggled.connect(self.photo_choose)
        mw.ui.part_recognition_radioButton.toggled.connect(self.photo_choose)
        mw.ui.all_recognition_radioButton.toggled.connect(self.photo_choose)
        mw.ui.pre_btn.clicked.connect(self.pre_photo)
        mw.ui.next_btn.clicked.connect(self.next_photo)
        mw.ui.tableWidget.itemChanged.connect(self.table_item_changed)
        mw.ui.select_dir_radioButton.toggled.connect(self.dir_choose)
        mw.ui.current_dir_radioButton.toggled.connect(self.dir_choose)

        mw.ui.all_photo_radioButton.setEnabled(False)
        mw.ui.part_recognition_radioButton.setEnabled(False)
        mw.ui.all_recognition_radioButton.setEnabled(False)

        mw.ui.photo_view.resizeEvent = self.resize_image
        mw.ui.photo_view.setAlignment(QtCore.Qt.AlignCenter)

        mw.ui.pre_btn.setStyleSheet(mw.button_style_sheet)
        mw.ui.next_btn.setStyleSheet(mw.button_style_sheet)

        mw.ui.verifycheckBox.stateChanged.connect(self.checked)

    @staticmethod
    @catch_exception
    def resize_image(event):
        if not PhotoDescription.pix_map:
            return
        size = event.size()
        w, h = size.width() - 1, size.height() - 1  # wow
        pix_map = PhotoDescription.pix_map.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        mw.ui.photo_view.setPixmap(pix_map)

    @staticmethod
    @catch_exception
    def photo_choose(check_state):
        if check_state is False:
            return
        mw.ui.tabWidget.setCurrentIndex(2)
        PhotoDescription.photo_type = PhotoDescription.photo_radio_map[mw.sender().objectName()]
        photo_info_list = mw.interaction.get_photos_info(PhotoDescription.photo_type, PhotoDescription.dir_type)
        mw.photo_list = list(map(lambda d: d['photo_path'], photo_info_list))
        mw.photo_info_dict = {d['photo_path']: d for d in photo_info_list}
        PhotoDescription.tmp_info = {}
        mw.current_photo_id = 0
        PhotoDescription._display_recognizable()

    @staticmethod
    @catch_exception
    def dir_choose(check_state):
        if check_state is False:
            return
        dir_scope, PhotoDescription.dir_type = PhotoDescription.dir_radio_map[mw.sender().objectName()]
        mw.ui.all_photo_radioButton.setText(f'显示{dir_scope}所有照片(Alt+Q)')
        mw.ui.part_recognition_radioButton.setText(f'显示{dir_scope}部分识别照片(Alt+W)')
        mw.ui.all_recognition_radioButton.setText(f'显示{dir_scope}全部识别照片(Alt+E)')
        mw.ui.all_photo_radioButton.setShortcut('Alt+Q')
        mw.ui.part_recognition_radioButton.setShortcut('Alt+W')
        mw.ui.all_recognition_radioButton.setShortcut('Alt+E')

    @staticmethod
    @catch_exception
    def pre_photo():
        if mw.ui.tabWidget.currentIndex() != 2:
            mw.ui.tabWidget.setCurrentIndex(2)
            return
        PhotoDescription.tmp_info[mw.photo_list[mw.current_photo_id]] = mw.get_name_info()
        if mw.current_photo_id > 0:
            mw.current_photo_id -= 1
            PhotoDescription._display_recognizable()

    @staticmethod
    @catch_exception
    def next_photo():
        if mw.ui.tabWidget.currentIndex() != 2:
            mw.ui.tabWidget.setCurrentIndex(2)
            return
        PhotoDescription.tmp_info[mw.photo_list[mw.current_photo_id]] = mw.get_name_info()
        if mw.current_photo_id < len(mw.photo_list) - 1:
            mw.current_photo_id += 1
            PhotoDescription._display_recognizable()

    @staticmethod
    @catch_exception
    def _create_button(name, ico_path):
        button = QtWidgets.QPushButton(QIcon(QPixmap(ico_path)), name, mw.ui.tableWidget)
        button.setFlat(True)
        return button

    @staticmethod
    @catch_exception
    def add():
        row = mw.ui.tableWidget.rowCount() - 1
        del_button = PhotoDescription._create_button('删除', PhotoDescription.del_icon_path)
        del_button.clicked.connect(lambda: PhotoDescription.delete(row))
        mw.ui.tableWidget.setCellWidget(row, 2, del_button)
        add_button = PhotoDescription._create_button('添加', PhotoDescription.add_icon_path)
        add_button.clicked.connect(PhotoDescription.add)
        mw.ui.tableWidget.insertRow(row + 1)
        for col in range(2):
            item = QTableWidgetItem('')
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            mw.ui.tableWidget.setItem(row+1, col, item)
        mw.ui.tableWidget.setCellWidget(row+1, 2, add_button)
        mw.ui.verifycheckBox.setCheckState(Qt.Unchecked)
        mw.check_state_dict[mw.photo_list[mw.current_photo_id]] = Qt.Unchecked

    @staticmethod
    @catch_exception
    def delete(row):
        mw.ui.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        mw.ui.tableWidget.removeRow(row)
        for r in range(row, mw.ui.tableWidget.rowCount() - 1):
            mw.ui.tableWidget.cellWidget(r, 2).clicked.disconnect()
            PhotoDescription._connect(mw.ui.tableWidget.cellWidget(r, 2), r)
        mw.ui.verifycheckBox.setCheckState(Qt.Unchecked)
        mw.check_state_dict[mw.photo_list[mw.current_photo_id]] = Qt.Unchecked
        mw.ui.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.CurrentChanged)

    @staticmethod
    @catch_exception
    def table_item_changed():
        mw.ui.verifycheckBox.setCheckState(Qt.Unchecked)
        mw.check_state_dict[mw.photo_list[mw.current_photo_id]] = Qt.Unchecked

    @staticmethod
    @catch_exception
    def _connect(button, row):
        button.clicked.connect(lambda: PhotoDescription.delete(row))

    @staticmethod
    @catch_exception
    def _display_recognizable():
        if not mw.photo_list:
            mw.ui.photo_view.setText('没有照片可显示')
            return
        photo_path = mw.photo_list[mw.current_photo_id]
        PhotoDescription.pix_map = QPixmap(photo_path)
        faces_data = mw.photo_info_dict.get(photo_path).get('faces')
        name_info_list, coordinate_list = PhotoDescription._conversion_data(faces_data)
        tmp_name_info_list = PhotoDescription.tmp_info.get(photo_path)
        mw.ui.tableWidget.itemChanged.disconnect()
        if tmp_name_info_list is None:
            PhotoDescription._update_table_widget(name_info_list)
        else:
            PhotoDescription._update_table_widget(tmp_name_info_list)
        mw.ui.tableWidget.itemChanged.connect(PhotoDescription.table_item_changed)
        PhotoDescription._mark_face(coordinate_list)
        pix_map = PhotoDescription.pix_map.scaled(mw.ui.photo_view.size(), Qt.KeepAspectRatio,
                                                  Qt.SmoothTransformation)
        mw.ui.photo_view.setPixmap(pix_map)
        mw.ui.photo_index_label.setText('{}/{}'.format(mw.current_photo_id + 1, len(mw.photo_list)))
        PhotoDescription._set_verify_checkbox(photo_path)
        mw.view.display_photo(photo_path)

    @staticmethod
    @catch_exception
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

    @staticmethod
    @catch_exception
    def _update_table_widget(name_info_list):
        for row in range(mw.ui.tableWidget.rowCount(), -1, -1):
            mw.ui.tableWidget.removeRow(row)
        row = -1
        for row, (id_, name) in enumerate(name_info_list):
            mw.ui.tableWidget.insertRow(row)
            for col, item in enumerate([id_, name]):
                item = QTableWidgetItem(item)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                mw.ui.tableWidget.setItem(row, col, item)
            del_button = PhotoDescription._create_button('删除', PhotoDescription.del_icon_path)
            PhotoDescription._connect(del_button, row)
            mw.ui.tableWidget.setCellWidget(row, 2, del_button)
        mw.ui.tableWidget.insertRow(row+1)
        for col in range(2):
            item = QTableWidgetItem('')
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            mw.ui.tableWidget.setItem(row+1, col, item)
        add_button = PhotoDescription._create_button('添加', PhotoDescription.add_icon_path)
        add_button.clicked.connect(PhotoDescription.add)
        mw.ui.tableWidget.setCellWidget(row+1, 2, add_button)

    @staticmethod
    @catch_exception
    def _set_verify_checkbox(photo_path):
        photo_info = mw.photo_info_dict.get(photo_path)
        if photo_info:
            verify_state_code = photo_info.get('verify_state', 0)
            if verify_state_code == 1:
                original_verify_state = Qt.Checked
            else:
                original_verify_state = Qt.Unchecked
        else:
            original_verify_state = Qt.Unchecked
        current_check_state = mw.check_state_dict.get(photo_path, original_verify_state)
        if current_check_state == Qt.Checked:
            mw.ui.verifycheckBox.stateChanged.disconnect()
            mw.ui.verifycheckBox.setCheckState(Qt.Checked)
            mw.ui.verifycheckBox.stateChanged.connect(PhotoDescription.checked)
        else:
            mw.ui.verifycheckBox.setCheckState(Qt.Unchecked)

    @staticmethod
    @catch_exception
    def _mark_face(coordinate_list):
        painter = QPainter(PhotoDescription.pix_map)
        for id_, coordinate in coordinate_list:
            x, y, w, h = coordinate
            font = QFont()
            font.setPixelSize(h/3)
            painter.setFont(font)
            pen = QPen(QtCore.Qt.yellow)
            painter.setPen(pen)
            pos = QRect(x, y, w, h)
            painter.drawText(pos, 0, f'{id_}')
            pen = QPen(QtCore.Qt.red)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(x, y, w, h)

    @staticmethod
    @catch_exception
    def checked():
        if mw.ui.verifycheckBox.isChecked() and mw.photo_list:
            name_list = mw.get_name_info()
            photo_path = mw.photo_list[mw.current_photo_id]
            size = mw.ui.photo_view.size()
            checked_info = {
                "path": photo_path,
                "arch_code": mw.ui.arch_code_in_photo.text(),
                "faces": mw.photo_info_dict.get(photo_path).get('faces'),
                "table_widget": [{'id': i, 'name': n} for i, n in name_list],
                "label_size": (size.width(), size.height())
            }
            mw.interaction.checked(checked_info)
            mw.check_state_dict[photo_path] = Qt.Checked


class GroupDescription(object):
    current_work_path = ''
    line_edit_prefix = '__line_edit__'
    # type_in_icon_path = 'icon/type_in.png'

    def __init__(self):
        height = int(mw.dt_height*30/1080)
        mw.ui.treeWidget.setStyleSheet('#treeWidget::item{height:%spx;}' % (height + 5))
        mw.ui.open_dir_btn.clicked.connect(self.display_dir)
        mw.ui.treeWidget.itemClicked.connect(self.item_click)
        mw.ui.add_folder_btn.clicked.connect(self.add_folder_item)
        mw.ui.cancel_folder_btn.clicked.connect(self.cancel_folder_item)
        mw.ui.save_group_btn.clicked.connect(self.save_group)

        mw.ui.add_folder_btn.setStyleSheet(mw.button_style_sheet)
        mw.ui.cancel_folder_btn.setStyleSheet(mw.button_style_sheet)
        mw.ui.save_group_btn.setStyleSheet(mw.button_style_sheet)

        self.display_group()

    @staticmethod
    @catch_exception
    def save_group():
        group_in = GroupInputData()
        for k in group_in.__dict__.keys():
            widget = getattr(mw.ui, k+'_in_group')
            if isinstance(widget, QComboBox):
                value = widget.currentText()
            elif isinstance(widget, QTextEdit):
                value = widget.toPlainText()
            else:
                value = widget.text()
            setattr(group_in, k, value)
        mw.controller.save_group(group_in)

    @staticmethod
    @catch_exception
    def display_dir():
        current_work_path = QFileDialog.getExistingDirectory(mw.ui.treeWidget, "选择文件夹",
                                                             options=QFileDialog.ShowDirsOnly)
        if not current_work_path:
            return
        mw.ui.tabWidget.setCurrentIndex(0)
        GroupDescription.current_work_path = os.path.abspath(current_work_path)
        mw.ui.dir_lineEdit.setText(GroupDescription.current_work_path)
        overlay = Overlay(mw.ui.treeWidget, '初始化中', dynamic=True)
        overlay.show()
        while 1:
            if mw.interaction != typing.Any:
                break
            else:
                QApplication.processEvents()
        overlay.hide()
        arch_code_info = mw.interaction.get_arch_code(GroupDescription.current_work_path)
        if arch_code_info and arch_code_info.get('root'):
            GroupDescription._generate_tree_by_data(arch_code_info)
        else:
            GroupDescription._generate_tree_by_path(GroupDescription.current_work_path)
        GroupDescription._reset_state()

    @staticmethod
    @catch_exception
    def _reset_state():
        mw.ui.radio_btn_group.setExclusive(False)
        for rb in [mw.ui.all_photo_radioButton,
                   mw.ui.part_recognition_radioButton,
                   mw.ui.all_recognition_radioButton]:
            rb.setEnabled(True)
            rb.setChecked(False)
        mw.ui.radio_btn_group.setExclusive(True)

        mw.ui.recogni_btn.setEnabled(True)

        for label in mw.rcn_info_label_dict.values():
            label.clear()
        mw.ui.progressBar.setValue(0)
        mw.ui.arch_code_in_photo.clear()
        mw.ui.photo_view.clear()
        for row in range(mw.ui.tableWidget.rowCount(), -1, -1):
            mw.ui.tableWidget.removeRow(row)
        mw.ui.photo_index_label.clear()

        mw.run_state = RunState.stop
        mw.ui.pausecontinue_btn.setText('停止')
        mw.ui.run_state_label.setText("停止")

        mw.ui.verifycheckBox.setCheckState(False)

    @staticmethod
    @catch_exception
    def item_click(item):
        if item.text(0) == GroupDescription.current_work_path:
            return
        if item.checkState(0) == Qt.Unchecked:
            item.setCheckState(0, Qt.Checked)
        else:
            item.setCheckState(0, Qt.Unchecked)

    @staticmethod
    @catch_exception
    def add_folder_item():
        arch_code_info = {
            "root": {},
            "children": {}
        }
        root_item = mw.ui.treeWidget.invisibleRootItem().child(0)
        if root_item is None:
            return
        item_iterator = QTreeWidgetItemIterator(mw.ui.treeWidget)
        items_value = item_iterator.value()
        for i in range(items_value.childCount()):
            item = items_value.child(i)
            if item.checkState(0) == Qt.Checked:
                path = item.text(0)
                line_edit = mw.ui.treeWidget.itemWidget(item, 1)
                arch_code = line_edit.text()
                arch_code_info["children"].update({os.path.join(GroupDescription.current_work_path, path): arch_code})
        mw.interaction.set_arch_code(arch_code_info)
        GroupDescription._reset_state()

    @staticmethod
    @catch_exception
    def cancel_folder_item():
        item_value = QTreeWidgetItemIterator(mw.ui.treeWidget).value()
        if item_value is None:
            return
        child_count = item_value.childCount()
        for i in range(child_count):
            if item_value.child(i).checkState(0) == Qt.Checked:
                item_value.child(i).setCheckState(0, Qt.Unchecked)

    @staticmethod
    @catch_exception
    def _generate_dir_tree(root_arch_info, file_arch_list):
        root_path, root_arch_code = root_arch_info
        _, volume_name = os.path.split(root_path)
        mw.ui.treeWidget.setColumnWidth(0, int(520*mw.dt_width/1920))  # 设置列宽
        # mw.ui.treeWidget.setColumnWidth(1, int(60*mw.dt_width/1920))  # 设置列宽
        mw.ui.treeWidget.clear()
        root = QTreeWidgetItem(mw.ui.treeWidget)
        root.setText(0, root_path)
        # description_btn = GroupDescription._gen_description_btn()
        # mw.ui.treeWidget.setItemWidget(root, 1, description_btn)
        for name, arch_code in file_arch_list:
            child = QTreeWidgetItem(root)
            child.setText(0, name)
            description_btn = GroupDescription._gen_description_btn()
            GroupDescription._connect(description_btn, root_path + '\\' + name)
            mw.ui.treeWidget.setItemWidget(child, 1, description_btn)
            child.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            child.setCheckState(0, Qt.Checked)
        mw.ui.treeWidget.expandAll()

    @staticmethod
    @catch_exception
    def _gen_description_btn():
        description_btn = QtWidgets.QPushButton(
            ' ',
            mw.ui.treeWidget
        )
        font = QFont()
        font.setFamily("新宋体")
        font.setPointSize(14)
        description_btn.setFont(font)
        description_btn.setStyleSheet("text-align: left; padding-left: 18px;")
        description_btn.setFlat(True)
        return description_btn

    @staticmethod
    @catch_exception
    def _connect(button, path):
        button.clicked.connect(lambda: GroupDescription.display_group(path))

    @staticmethod
    @catch_exception
    def display_group(path=''):
        if path:
            group_name = os.path.split(path)[1]
            mw.controller.get_group(group_name)
        else:
            group_name = ''
        mw.view.display_group_in_description()
        mw.ui.group_path_in_group.setText(group_name)

    @staticmethod
    @catch_exception
    def _generate_tree_by_path(root_path):
        file_list = filter(lambda p: os.path.isdir(os.path.join(root_path, p)), os.listdir(root_path))
        root_arch_info = (root_path, '')
        file_arch_list = [(fp, '') for fp in file_list]
        GroupDescription._generate_dir_tree(root_arch_info, file_arch_list)

    @staticmethod
    @catch_exception
    def _generate_tree_by_data(arch_code_info):
        root_arch = arch_code_info['root']
        root_arch_info = list(root_arch.items())[0]
        root_path = root_arch_info[0]
        children_arch = {p: '' for p in filter(lambda p: os.path.isdir(os.path.join(root_path, p)),
                                               os.listdir(root_path))}
        children_arch.update({(fp[len(root_path)+1:], an) for fp, an in arch_code_info['children'].items()})
        arch_list = children_arch.items()
        GroupDescription._generate_dir_tree(root_arch_info, arch_list)


class Training(object):
    def __init__(self):
        mw.ui.train_btn.clicked.connect(self.start_training)
        mw.ui.train_btn.setStyleSheet(mw.button_style_sheet)

    @staticmethod
    @catch_exception
    def start_training():
        training_info = mw.interaction.start_training()
        model_acc = training_info.get('model_acc')
        if model_acc == -1:
            mw.msg_box('训练数据不存在，请核验人脸信息，收集数据')
        elif model_acc == -2:
            mw.msg_box('数据只有一类标签，至少需要两类标签')
        else:
            mw.ui.model_acc_label.setText(str(model_acc))
        untrained_photo_num = mw.interaction.get_untrained_photo_num()
        mw.ui.untrained_num_label.setText(str(untrained_photo_num))


class ArchBrowser(object):
    pix_map = None
    group_name = None

    def __init__(self):
        list_widget = mw.ui.photo_list_widget
        list_widget.setViewMode(QListWidget.IconMode)
        list_widget.setIconSize(QSize(200, 150))
        # list_widget.setFixedHeight(235)
        list_widget.setWrapping(False)  # 只一行显示
        list_widget.itemClicked.connect(self.display_photo)

        mw.ui.photo_view_in_arch.resizeEvent = self.resize_image
        mw.ui.photo_view_in_arch.setAlignment(QtCore.Qt.AlignCenter)
        mw.ui.arch_tree_view_browse.clicked.connect(self.show_group)
        mw.ui.order_combobox_browse.currentTextChanged.connect(self.display_arch)

    @staticmethod
    @catch_exception
    def resize_image(event):
        if not ArchBrowser.pix_map:
            return
        size = event.size()
        w, h = size.width() - 1, size.height() - 1  # wow
        pix_map = ArchBrowser.pix_map.scaled(w, h,
                                             Qt.KeepAspectRatio,
                                             Qt.SmoothTransformation)
        mw.ui.photo_view_in_arch.setPixmap(pix_map)

    @staticmethod
    @catch_exception
    def show_group(index):
        if index.child(0, 0).data():  # 点击的不是组名则返回
            return
        ArchBrowser.group_name = index.data()
        mw.controller.get_group(ArchBrowser.group_name)
        mw.view.display_group_in_arch_browse()
        mw.ui.photo_view_in_arch.clear()
        ArchBrowser._list_photo_thumb()

    @staticmethod
    @catch_exception
    def _list_photo_thumb():
        mw.ui.photo_list_widget.clear()
        path = os.path.join(Setting.path, ArchBrowser.group_name, '*.*')
        for fp in glob.iglob(path):
            item = QListWidgetItem(QIcon(fp), os.path.split(fp)[1])
            mw.ui.photo_list_widget.addItem(item)
            QApplication.processEvents()

    @staticmethod
    @catch_exception
    def display_photo(item):
        photo_name = item.text()
        path = os.path.join(Setting.path, ArchBrowser.group_name, photo_name)
        ArchBrowser.pix_map = QPixmap(path)
        pix_map = ArchBrowser.pix_map.scaled(mw.ui.photo_view_in_arch.size(),
                                             Qt.KeepAspectRatio,
                                             Qt.SmoothTransformation)
        mw.ui.photo_view_in_arch.setPixmap(pix_map)

    @staticmethod
    @catch_exception
    def display_arch(text):
        mw.ui.order_combobox_transfer.setCurrentText(text)
        mw.view.display_arch(text)


class ArchTransfer(object):
    selected_arch_list = []

    def __init__(self):
        list_widget = mw.ui.selected_arch_list_widget
        list_widget.setViewMode(QListWidget.IconMode)
        list_widget.setIconSize(QSize(200, 150))
        list_widget.setResizeMode(QListWidget.Adjust)
        list_widget.itemDoubleClicked.connect(self.unselect_arch)

        mw.ui.order_combobox_transfer.currentTextChanged.connect(self.display_arch)
        mw.ui.arch_tree_view_transfer.doubleClicked.connect(self.select_arch)

    @staticmethod
    @catch_exception
    def display_arch(text):
        mw.ui.order_combobox_browse.setCurrentText(text)
        mw.view.display_arch(text)

    @staticmethod
    @catch_exception
    def select_arch(index):
        if index.child(0, 0).data():  # 点击的不是组名则返回
            return
        group_name = index.data()
        if group_name in ArchTransfer.selected_arch_list:
            return
        path = os.path.join(Setting.path, group_name, '*.*')
        for fp in glob.iglob(path):
            item = QListWidgetItem(QIcon(fp), group_name)
            mw.ui.selected_arch_list_widget.addItem(item)
            break
        ArchTransfer.selected_arch_list.append(group_name)

    @staticmethod
    @catch_exception
    def unselect_arch(item):
        row = mw.ui.selected_arch_list_widget.row(item)
        mw.ui.selected_arch_list_widget.takeItem(row)
        item_text = item.text()
        if item_text in ArchTransfer.selected_arch_list:
            ArchTransfer.selected_arch_list.remove(item_text)


class Setting(object):
    path = r'.\已著录'

    def __init__(self):
        pass


def init_parts():
    Recognition()
    PhotoDescription()
    GroupDescription()
    Training()
    ArchBrowser()
    ArchTransfer()
    Setting()
