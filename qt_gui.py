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
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qt.qt_ui import Ui_MainWindow


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


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.interaction = QtInteraction()

        Recognition(self)
        Picture(self)
        DirTree(self)
        Training(self)
        Checked(self)


class Recognition(object):
    def __init__(self, mw):
        for func_name, _ in inspect.getmembers(self, predicate=inspect.isfunction):
            setattr(MainWindow, func_name, getattr(self, func_name))
        mw.run_state = RunState.stop
        mw.ui.recogniButton.clicked.connect(mw.run)
        mw.ui.pausecontinueButton.clicked.connect(mw.pause_or_continue)
        mw.update_timer = QTimer()
        mw.update_timer.timeout.connect(mw.periodic_update)
        mw.update_timer.start(2000)

    @staticmethod
    @catch_exception
    def run(mw):
        mw.ui.tabWidget.setCurrentIndex(0)
        mw.ui.pausecontinueButton.setText('停止')
        mw.ui.run_state_label.setText("运行中...")
        if mw.run_state != RunState.running:
            mw.run_state = RunState.running
            mw.interaction.start()

    @staticmethod
    @catch_exception
    def pause_or_continue(mw):
        mw.ui.tabWidget.setCurrentIndex(0)
        if mw.run_state == RunState.running:
            mw.ui.pausecontinueButton.setText('继续')
            mw.ui.run_state_label.setText("暂停")
            mw.run_state = RunState.pause
            mw.interaction.pause()
        elif mw.run_state == RunState.pause:
            mw.ui.pausecontinueButton.setText('停止')
            mw.ui.run_state_label.setText("运行中...")
            mw.run_state = RunState.running
            mw.interaction.continue_run()
        else:
            pass

    @staticmethod
    @catch_exception
    def periodic_update(mw):
        if mw.run_state == RunState.running:
            if mw.ui.tabWidget.currentIndex() == 0:
                recognition_info = mw.interaction.get_recognition_info()
                rcn_info_label_dict = {
                    "recognition_rate": mw.ui.recognition_rate_label,
                    "recognized_face_num": mw.ui.recognized_face_label,
                    "part_recognized_pic_num": mw.ui.part_recognized_pic_label,
                    "all_recognized_pic_num": mw.ui.all_recognized_pic_label,
                    "handled_pic_num": mw.ui.handled_pic_label,
                    "unhandled_pic_num": mw.ui.unhandled_pic_label
                }
                for key, value in recognition_info.items():
                    rcn_info_label_dict[key].setText(str(value))


class Picture(object):
    def __init__(self, mw):
        for func_name, _ in inspect.getmembers(self, predicate=inspect.isfunction):
            setattr(MainWindow, func_name, getattr(self, func_name))
        mw.radio_map = {'all_pic_radioButton': 1,
                        'part_recognition_radioButton': 2,
                        'all_recognition_radioButton': 3}
        mw.pix_map = None
        mw.pic_list = []
        mw.pic_info_dict = {}
        mw.current_pic_id = 0
        mw.ui.pic_view.setScaledContents(True)
        mw.ui.all_pic_radioButton.toggled.connect(mw.pic_choose)
        mw.ui.part_recognition_radioButton.toggled.connect(mw.pic_choose)
        mw.ui.all_recognition_radioButton.toggled.connect(mw.pic_choose)
        mw.ui.preButton.clicked.connect(mw.pre_pic)
        mw.ui.nextButton.clicked.connect(mw.next_pic)
        mw.ui.all_pic_radioButton.setEnabled(False)
        mw.ui.part_recognition_radioButton.setEnabled(False)
        mw.ui.all_recognition_radioButton.setEnabled(False)

    @staticmethod
    @catch_exception
    def pic_choose(mw):
        mw.ui.tabWidget.setCurrentIndex(1)
        pic_info_list = mw.interaction.get_pics_info(pic_type=mw.radio_map[mw.sender().objectName()])
        mw.pic_list = list(map(lambda d: d['img_path'], pic_info_list))
        mw.pic_info_dict = {d['img_path']: d for d in pic_info_list}
        mw.current_pic_id = 0
        mw.display_recognizable()

    @staticmethod
    @catch_exception
    def pre_pic(mw):
        if mw.current_pic_id > 0:
            mw.current_pic_id -= 1
            mw.display_recognizable()

    @staticmethod
    @catch_exception
    def next_pic(mw):
        if mw.current_pic_id < len(mw.pic_list) - 1:
            mw.current_pic_id += 1
            mw.display_recognizable()

    @staticmethod
    @catch_exception
    def display_recognizable(mw):
        pic_path = mw.pic_list[mw.current_pic_id]
        face_coordinates_list = json.loads(mw.pic_info_dict.get(pic_path).get('faces'))
        for row in range(mw.ui.tableWidget.rowCount(), -1, -1):
            mw.ui.tableWidget.removeRow(row)
        mw.pix_map = QPixmap(mw.pic_list[mw.current_pic_id])
        for row, face_info in enumerate(face_coordinates_list):
            mw.ui.tableWidget.insertRow(row)
            id_ = str(face_info.get('id'))
            name = face_info.get('name')
            coordinate = json.loads(face_info.get('box'))
            for col, item in enumerate([id_, name]):
                item = QTableWidgetItem(item)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                mw.ui.tableWidget.setItem(row, col, item)
            mw.mark_face(name, coordinate)
        mw.ui.arch_num_lineEdit.setText(mw.pic_info_dict.get(pic_path).get('archival_num'))
        mw.ui.theme_textEdit.setText(mw.pic_info_dict.get(pic_path).get('subject'))
        mw.ui.pic_view.setPixmap(mw.pix_map)
        mw.ui.pic_index_label.setText('{}/{}'.format(mw.current_pic_id + 1, len(mw.pic_list)))
        mw.ui.verifycheckBox.setCheckState(Qt.Unchecked)

    @staticmethod
    @catch_exception
    def mark_face(mw, name, coordinate):
        x, y, l, h = coordinate
        painter = QPainter(mw.pix_map)
        pen = QPen(QtCore.Qt.blue)
        painter.setPen(pen)
        pos = QPoint(x, y+h+15)
        painter.drawText(pos, name)
        pen = QPen(QtCore.Qt.red)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(x, y, l, h)


class DirTree(object):
    def __init__(self, mw):
        for func_name, _ in inspect.getmembers(self, predicate=inspect.isfunction):
            setattr(MainWindow, func_name, getattr(self, func_name))
        mw.current_work_path = ''
        mw.volume_dict = {}
        mw.ui.dirpushButton.clicked.connect(mw.display_dir)
        mw.ui.treeWidget.itemChanged.connect(mw.select_folder_item)
        mw.ui.add_folder_btn.clicked.connect(mw.add_folder_item)
        mw.ui.cancel_folder_btn.clicked.connect(mw.cancel_folder_item)

    @staticmethod
    @catch_exception
    def generate_tree_data(mw, root_volume_path):
        _, volume_name = os.path.split(root_volume_path)
        mw.ui.treeWidget.setColumnWidth(0, 150)  # 设置列宽
        mw.ui.treeWidget.clear()
        root = QTreeWidgetItem(mw.ui.treeWidget)
        root.setText(0, root_volume_path)
        root.setText(1, "编辑")
        root.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)  # 设为可编辑
        list_file = os.listdir(root_volume_path)
        for name in list_file:
            child1 = QTreeWidgetItem(root)
            child1.setText(0, name)
            child1.setText(1, "编辑")
            child1.setCheckState(0, Qt.Checked)
            child1.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)  # 设为可编辑
        mw.ui.treeWidget.expandAll()
        return volume_name

    @staticmethod
    @catch_exception
    def display_dir(mw):
        mw.ui.tabWidget.setCurrentIndex(2)
        current_work_path = QFileDialog.getExistingDirectory(mw.ui.treeWidget, "选择文件夹",
                                                             options=QFileDialog.ShowDirsOnly)
        mw.current_work_path = os.path.abspath(current_work_path)
        mw.generate_tree_data(mw.current_work_path)
        mw.ui.all_pic_radioButton.setEnabled(True)
        mw.ui.part_recognition_radioButton.setEnabled(True)
        mw.ui.all_recognition_radioButton.setEnabled(True)

    @staticmethod
    @catch_exception
    def select_folder_item(mw, item):
        path = item.text(0)
        mw.volume_dict[path] = item.text(1)
        if (item.checkState(0) == Qt.Unchecked) and (path != mw.current_work_path):
            mw.volume_dict.pop(path, None)

    @staticmethod
    @catch_exception
    def cancel_folder_item(mw):
        item = QTreeWidgetItemIterator(mw.ui.treeWidget)
        child_count = item.value().childCount()
        for i in range(child_count):
            if item.value().child(i).checkState(0) == Qt.Checked:
                item.value().child(i).setCheckState(0, Qt.Unchecked)

    @staticmethod
    @catch_exception
    def add_folder_item(mw):
        arch_num_info = {
            "root": {},
            "children": {}
        }
        for path, num in mw.volume_dict.items():
            if os.sep in path:
                arch_num_info["root"].update({path: num})
            else:
                arch_num_info["children"].update({os.path.join(mw.current_work_path, path): num})
        mw.interaction.set_archival_number(arch_num_info)


class Training(object):
    def __init__(self, mw):
        for func_name, _ in inspect.getmembers(self, predicate=inspect.isfunction):
            setattr(MainWindow, func_name, getattr(self, func_name))
        mw.ui.train_pushButton.clicked.connect(mw.set_training_params)

    @staticmethod
    @catch_exception
    def set_training_params(mw):
        training_params = {
            "threshold": mw.ui.thresh_lineEdit.text(),
            "distance": mw.ui.distance_lineEdit.text()
        }
        mw.interaction.set_training_params(training_params)


class Checked(object):
    def __init__(self, mw):
        for func_name, _ in inspect.getmembers(self, predicate=inspect.isfunction):
            setattr(MainWindow, func_name, getattr(self, func_name))
        mw.ui.verifycheckBox.stateChanged.connect(mw.checked)

    @staticmethod
    @catch_exception
    def checked(mw):
        if mw.ui.verifycheckBox.isChecked() and mw.pic_list:
            name_list = []
            for row in range(mw.ui.tableWidget.rowCount()):
                id_ = mw.ui.tableWidget.item(row, 0).text()
                name = mw.ui.tableWidget.item(row, 1).text()
                name_list.append({'id': id_, 'name': name})
            pic_path = mw.pic_list[mw.current_pic_id]
            checked_info = {
                "path": pic_path,
                "arch_num": mw.ui.arch_num_lineEdit.text(),
                "theme": mw.ui.theme_textEdit.toPlainText(),
                "faces": mw.pic_info_dict.get(pic_path).get('faces'),
                "table_widget": name_list
            }
            mw.interaction.checked(checked_info)


if __name__ == "__main__":
    if (len(sys.argv) > 1) and (sys.argv[1] in ('-t', '--test')):
        from qt.qt_interaction import QtInteraction
    else:
        from recognition.qt_interaction import QtInteraction

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
