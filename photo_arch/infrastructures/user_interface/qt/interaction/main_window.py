# -*- coding: utf-8 -*-
"""
@file: main_window.py
@desc:
@author: Jaden Wu
@time: 2020/8/20 11:14
"""
import sys
import inspect
from threading import Thread
import typing
from collections import defaultdict
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from photo_arch.adapters.controller import Controller
from photo_arch.adapters.sql.repo import Repo
from photo_arch.adapters.presenter import Presenter, ViewModel
from photo_arch.infrastructures.databases.db_setting import engine, make_session
from photo_arch.infrastructures.user_interface.qt.ui.qt_ui import Ui_MainWindow
from photo_arch.infrastructures.user_interface.ui_interface import UiInterface


class RecognizeState(object):
    stop = 0
    running = 1
    pause = 2


def static(method):
    return lambda *a: method(*a)


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
            from photo_arch.infrastructures.user_interface.qt.if_simulation.\
                qt_interaction import QtInteraction
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
        self.view = View(self)

        self.interaction: UiInterface = typing.Any
        self.controller = get_controller()
        self.init_recognition = InitRecognition(self)
        self.init_recognition.start()

        self.photo_list = []
        self.photo_info_dict = {}

        self.rcn_info_label_dict = {
            "recognition_rate": self.ui.recognition_rate_label,
            "recognized_face_num": self.ui.recognized_face_label,
            "part_recognized_photo_num": self.ui.part_recognized_photo_label,
            "all_recognized_photo_num": self.ui.all_recognized_photo_label,
            "handled_photo_num": self.ui.handled_photo_label,
            "unhandled_photo_num": self.ui.unhandled_photo_label
        }
        self.run_state = RecognizeState.stop
        self.ui.tabWidget.currentChanged.connect(self.tab_change)
        self.ui.tabWidget.setCurrentIndex(2)
        self.ui.tabWidget.setCurrentIndex(0)

        desktop = app.desktop()
        self.dt_width, self.dt_height = desktop.width(), desktop.height()
        self.button_style_sheet = "padding-left: {0}px;" \
                                  "padding-right:{0}px;" \
                                  "padding-top:8px; " \
                                  "padding-bottom: 8px;".format(int(30*self.dt_width/1920))

        self.photo_type = 1
        self.dir_type = 1

    @catch_exception
    def tab_change(self, tab_id):
        if tab_id == 3:  # 选中“模型训练”tab
            if self.interaction != typing.Any:
                untrained_photo_num = self.interaction.get_untrained_photo_num()
                self.ui.untrained_num_label.setText(str(untrained_photo_num))
        elif tab_id == 4:  # 选中“档案浏览”tab
            self.controller.browse_arch()
            self.view.display_browse_arch(self.ui.order_combobox_browse.currentText())
        elif tab_id == 5:  # 选中“档案移交”tab
            self.controller.browse_arch()
            self.view.display_transfer_arch(self.ui.order_combobox_transfer.currentText())
        else:
            pass

    @catch_exception
    def msg_box(self, msg: str):
        QMessageBox().warning(self.ui.centralwidget, '提示', msg, QMessageBox.Ok, QMessageBox.Ok)


class View(object):
    def __init__(self, mw_: MainWindow):
        self.mw = mw_
        self.view_model = view_model

    def _display_group(self, widget_suffix):
        for k, v in self.view_model.group.items():
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

    def display_group_in_description(self):
        self._display_group('_in_group')

    def display_group_in_arch_browse(self):
        self._display_group('_in_group_arch')

    def display_photo(self, photo_path):
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
            widget = getattr(self.mw.ui, f'{k}_in_photo')
            widget.setText(self.mw.photo_info_dict.get(photo_path).get(k, ''))

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

    def display_browse_arch(self, priority_key='年度'):
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
        self.mw.ui.arch_tree_view_browse.setModel(model)
        self.mw.ui.arch_tree_view_browse.expandAll()

    def display_transfer_arch(self, priority_key='年度'):
        data = defaultdict(lambda: defaultdict(dict))
        for gi in self.view_model.arch:
            fc = gi.get('fonds_code')
            ye = gi.get('year')
            rp = gi.get('retention_period')
            if priority_key == '年度':
                data[fc][ye] = rp
            else:
                data[fc][rp] = ye
        model = QStandardItemModel()
        model.setHorizontalHeaderItem(0, QStandardItem("照片档案"))
        self._fill_model_from_dict(model.invisibleRootItem(), data)
        self.mw.ui.arch_tree_view_transfer.setModel(model)
        self.mw.ui.arch_tree_view_transfer.expandAll()

    def display_setting(self):
        pass
