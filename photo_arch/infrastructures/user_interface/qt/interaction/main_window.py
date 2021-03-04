# -*- coding: utf-8 -*-
"""
@file: main_window.py
@desc: 主窗体
@author: Jaden Wu
@time: 2020/8/20 11:14
"""
import sys
from threading import Thread
import typing

from PySide2 import QtWidgets, QtCore, QtGui

from photo_arch.infrastructures.user_interface.qt.ui.qt_ui import Ui_MainWindow
from photo_arch.infrastructures.user_interface.ui_interface import UiInterface


class RecognizeState(object):
    stop = 0
    running = 1
    pause = 2


class InitRecognition(Thread):
    def __init__(self, mw_instance):
        self.mw_instance = mw_instance
        super().__init__()

    def run(self) -> None:
        if (len(sys.argv) > 1) and (sys.argv[1] in ('-t', '--test')):
            from photo_arch.infrastructures.user_interface.if_simulation.\
                interaction import Interaction
        else:
            from recognition.qt_interaction import QtInteraction as Interaction
        self.mw_instance.interaction = Interaction()


class Overlay(QtWidgets.QWidget):
    def __init__(self, parent, text, is_dynamic=True, max_dot_num=3):
        QtWidgets.QWidget.__init__(self, parent)
        self.setWindowFlag(QtGui.Qt.WindowStaysOnTopHint)
        self.resize(parent.size())
        if is_dynamic:
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
        painter = QtGui.QPainter(self)
        painter.setFont(QtGui.QFont('新宋体', 15))
        painter.drawText(self.rect(), QtGui.Qt.AlignCenter, self.text)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.interaction: UiInterface = typing.Any
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
        self.ui.tabWidget.setCurrentWidget(self.ui.photo_tab)
        self.ui.tabWidget.setCurrentWidget(self.ui.group_tab)

        desktop = app.desktop()
        self.dt_width, self.dt_height = desktop.width(), desktop.height()

        self.photo_type = 1
        self.dir_type = 1

        self.ui.tabWidget.setAttribute(QtGui.Qt.WA_StyledBackground)

    def msg_box(self, msg: str, msg_type: str = 'warn'):
        if msg_type == 'warn':
            self.warn_msg(msg)
        elif msg_type == 'info':
            self.info_msg(msg)
        else:
            pass

    def warn_msg(self, msg):
        QtWidgets.QMessageBox().warning(self.ui.centralwidget, '提示', msg,
                                        QtWidgets.QMessageBox.Ok,
                                        QtWidgets.QMessageBox.Ok)

    def info_msg(self, msg):
        QtWidgets.QMessageBox().information(self.ui.centralwidget, '提示', msg,
                                            QtWidgets.QMessageBox.Ok,
                                            QtWidgets.QMessageBox.Ok)

    def overlay(self, widget, msg='后台初始化未完成，请稍等', is_dynamic=True):
        overlay = Overlay(widget, msg, is_dynamic=is_dynamic)
        overlay.show()
        while 1:
            if self.interaction != typing.Any:
                break
            else:
                QtWidgets.QApplication.processEvents()
        overlay.hide()
