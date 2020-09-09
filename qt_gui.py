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
if (len(sys.argv) > 1) and (sys.argv[1] in ('-t', '--test')):
    from qt.qt_interaction import QtInteraction
else:
    from recognition.qt_interaction import QtInteraction


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

        self.pic_list = []
        self.current_pic_id = 0
        self.pic_info_dict = {}

    def msg_box(self, msg: str):
        QMessageBox.warning(self, '提示', msg, QMessageBox.Ok, QMessageBox.Ok)


class Recognition(object):
    run_state = RunState.stop
    rcn_info_label_dict = {
     "recognition_rate": 'recognition_rate_label',
     "recognized_face_num": 'recognized_face_label',
     "part_recognized_pic_num": 'part_recognized_pic_label',
     "all_recognized_pic_num": 'all_recognized_pic_label',
     "handled_pic_num": 'handled_pic_label',
     "unhandled_pic_num": 'unhandled_pic_label'
    }
    update_timer = QTimer()

    def __init__(self):
        mw.ui.recogniButton.clicked.connect(self.run)
        mw.ui.pausecontinueButton.clicked.connect(self.pause_or_continue)
        Recognition.update_timer.timeout.connect(self.periodic_update)
        Recognition.update_timer.start(1000)

    @staticmethod
    @catch_exception
    def run():
        mw.ui.tabWidget.setCurrentIndex(0)
        if Recognition.run_state != RunState.running:
            thresh = mw.ui.thresh_lineEdit.text()
            distance = mw.ui.distance_lineEdit.text()
            params = {
                "threshold": float(thresh) if thresh else 0.8,
                "distance": float(distance) if distance else 0.8
            }
            result = mw.interaction.start(params)
            if result.get('res') is True:
                Recognition.run_state = RunState.running
                mw.ui.pausecontinueButton.setText('停止')
                mw.ui.run_state_label.setText('运行中...')
            else:
                mw.msg_box(result.get('msg'))

    @staticmethod
    @catch_exception
    def pause_or_continue():
        mw.ui.tabWidget.setCurrentIndex(0)
        if Recognition.run_state == RunState.running:
            result = mw.interaction.pause()
            if result.get('res'):
                Recognition.run_state = RunState.pause
                mw.ui.pausecontinueButton.setText('继续')
                mw.ui.run_state_label.setText("暂停")
            else:
                mw.msg_box(result.get('msg'))

        elif Recognition.run_state == RunState.pause:
            result = mw.interaction.continue_run()
            if result.get('res'):
                Recognition.run_state = RunState.running
                mw.ui.pausecontinueButton.setText('停止')
                mw.ui.run_state_label.setText('运行中...')
            else:
                mw.msg_box(result.get('msg'))
        else:
            pass

    @staticmethod
    @catch_exception
    def periodic_update():
        if Recognition.run_state == RunState.running:
            if mw.ui.tabWidget.currentIndex() == 0:
                recognition_info = mw.interaction.get_recognition_info()
                for key, value in recognition_info.items():
                    getattr(mw.ui, Recognition.rcn_info_label_dict[key]).setText(str(value))


class Picture(object):
    radio_map = {'all_pic_radioButton': 1,
                 'part_recognition_radioButton': 2,
                 'all_recognition_radioButton': 3}
    pix_map = None

    def __init__(self):
        mw.ui.pic_view.setScaledContents(True)
        mw.ui.all_pic_radioButton.toggled.connect(self.pic_choose)
        mw.ui.part_recognition_radioButton.toggled.connect(self.pic_choose)
        mw.ui.all_recognition_radioButton.toggled.connect(self.pic_choose)
        mw.ui.preButton.clicked.connect(self.pre_pic)
        mw.ui.nextButton.clicked.connect(self.next_pic)

        mw.ui.all_pic_radioButton.setEnabled(False)
        mw.ui.part_recognition_radioButton.setEnabled(False)
        mw.ui.all_recognition_radioButton.setEnabled(False)

    @staticmethod
    @catch_exception
    def pic_choose(check_state):
        if check_state is False:
            return
        mw.ui.tabWidget.setCurrentIndex(1)
        pic_info_list = mw.interaction.get_pics_info(pic_type=Picture.radio_map[mw.sender().objectName()])
        mw.pic_list = list(map(lambda d: d['img_path'], pic_info_list))
        mw.pic_info_dict = {d['img_path']: d for d in pic_info_list}
        mw.current_pic_id = 0
        Picture._display_recognizable()

    @staticmethod
    @catch_exception
    def pre_pic():
        if mw.current_pic_id > 0:
            mw.current_pic_id -= 1
            Picture._display_recognizable()

    @staticmethod
    @catch_exception
    def next_pic():
        if mw.current_pic_id < len(mw.pic_list) - 1:
            mw.current_pic_id += 1
            Picture._display_recognizable()

    @staticmethod
    @catch_exception
    def _display_recognizable():
        if not mw.pic_list:
            return
        pic_path = mw.pic_list[mw.current_pic_id]
        face_coordinates_list = json.loads(mw.pic_info_dict.get(pic_path).get('faces'))
        for row in range(mw.ui.tableWidget.rowCount(), -1, -1):
            mw.ui.tableWidget.removeRow(row)
        Picture.pix_map = QPixmap(mw.pic_list[mw.current_pic_id])
        for row, face_info in enumerate(face_coordinates_list):
            mw.ui.tableWidget.insertRow(row)
            id_ = str(face_info.get('id'))
            name = face_info.get('name')
            coordinate = json.loads(face_info.get('box'))
            for col, item in enumerate([id_, name]):
                item = QTableWidgetItem(item)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                mw.ui.tableWidget.setItem(row, col, item)
            Picture._mark_face(id_, coordinate)
        mw.ui.arch_num_lineEdit.setText(mw.pic_info_dict.get(pic_path).get('archival_num'))
        mw.ui.theme_textEdit.setText(mw.pic_info_dict.get(pic_path).get('subject'))
        mw.ui.pic_view.setPixmap(Picture.pix_map)
        mw.ui.pic_index_label.setText('{}/{}'.format(mw.current_pic_id + 1, len(mw.pic_list)))
        mw.ui.verifycheckBox.setCheckState(Qt.Unchecked)

    @staticmethod
    @catch_exception
    def _mark_face(id_, coordinate):
        x1, y1, x2, y2 = coordinate
        x, y, w, h = x1, y1, (x2 - x1), (y2 - y1)
        painter = QPainter(Picture.pix_map)
        pen = QPen(QtCore.Qt.yellow)
        painter.setPen(pen)
        pos = QPoint(x + 5, y + 10)
        painter.drawText(pos, f'{id_}')
        pen = QPen(QtCore.Qt.red)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(x, y, w, h)


class DirTree(object):
    current_work_path = ''
    volume_dict = {}

    def __init__(self):
        mw.ui.dirpushButton.clicked.connect(self.display_dir)
        mw.ui.treeWidget.itemChanged.connect(self.select_folder_item)
        mw.ui.add_folder_btn.clicked.connect(self.add_folder_item)
        mw.ui.cancel_folder_btn.clicked.connect(self.cancel_folder_item)

    @staticmethod
    @catch_exception
    def _generate_dir_tree(root_arch_info, file_arch_list):
        root_path, root_arch_num = root_arch_info
        _, volume_name = os.path.split(root_path)
        mw.ui.treeWidget.setColumnWidth(0, 300)  # 设置列宽
        mw.ui.treeWidget.clear()
        root = QTreeWidgetItem(mw.ui.treeWidget)
        root.setText(0, root_path)
        root.setText(1, root_arch_num)
        root.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)  # 设为可编辑
        for name, arch_num in file_arch_list:
            child1 = QTreeWidgetItem(root)
            child1.setText(0, name)
            child1.setText(1, arch_num)
            child1.setCheckState(0, Qt.Checked)
            child1.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsUserCheckable)  # 设为可编辑
        mw.ui.treeWidget.expandAll()

    @staticmethod
    @catch_exception
    def _generate_tree_by_path(root_path):
        file_list = os.listdir(root_path)
        root_arch_info = (root_path, '编辑')
        file_arch_list = [(fp, '编辑') for fp in file_list]
        DirTree._generate_dir_tree(root_arch_info, file_arch_list)

    @staticmethod
    @catch_exception
    def _generate_tree_by_data(arch_num_info):
        root_arch_info = list(arch_num_info['root'].items())[0]
        file_arch_list = list(arch_num_info['children'].items())
        root_path = root_arch_info[0]
        arch_list = [(fp[len(root_path)+1:], an) for fp, an in file_arch_list]
        DirTree._generate_dir_tree(root_arch_info, arch_list)

    @staticmethod
    @catch_exception
    def display_dir():
        mw.ui.tabWidget.setCurrentIndex(2)
        current_work_path = QFileDialog.getExistingDirectory(mw.ui.treeWidget, "选择文件夹",
                                                             options=QFileDialog.ShowDirsOnly)
        DirTree.current_work_path = os.path.abspath(current_work_path)
        arch_num_info = mw.interaction.get_archival_number(DirTree.current_work_path)
        if arch_num_info:
            DirTree._generate_tree_by_data(arch_num_info)
        else:
            DirTree._generate_tree_by_path(DirTree.current_work_path)

        mw.ui.all_pic_radioButton.setEnabled(True)
        mw.ui.part_recognition_radioButton.setEnabled(True)
        mw.ui.all_recognition_radioButton.setEnabled(True)

    @staticmethod
    @catch_exception
    def select_folder_item(item):
        path = item.text(0)
        DirTree.volume_dict[path] = item.text(1)
        if (item.checkState(0) == Qt.Unchecked) and (path != DirTree.current_work_path):
            DirTree.volume_dict.pop(path, None)

    @staticmethod
    @catch_exception
    def cancel_folder_item():
        item = QTreeWidgetItemIterator(mw.ui.treeWidget)
        child_count = item.value().childCount()
        for i in range(child_count):
            if item.value().child(i).checkState(0) == Qt.Checked:
                item.value().child(i).setCheckState(0, Qt.Unchecked)

    @staticmethod
    @catch_exception
    def add_folder_item():
        arch_num_info = {
            "root": {},
            "children": {}
        }
        for path, num in DirTree.volume_dict.items():
            if os.sep in path:
                arch_num_info["root"].update({path: num})
            else:
                arch_num_info["children"].update({os.path.join(DirTree.current_work_path, path): num})
        mw.interaction.set_archival_number(arch_num_info)


class Training(object):
    def __init__(self):
        mw.ui.train_pushButton.clicked.connect(self.start_training)

    @staticmethod
    @catch_exception
    def start_training():
        training_info = mw.interaction.start_training()
        mw.ui.model_acc_label.setText(str(training_info.get('model_acc')))


class Checked(object):
    def __init__(self):
        mw.ui.verifycheckBox.stateChanged.connect(self.checked)

    @staticmethod
    @catch_exception
    def checked():
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


def init_parts():
    Recognition()
    Picture()
    DirTree()
    Training()
    Checked()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mw = MainWindow()
    init_parts()
    mw.show()
    sys.exit(app.exec_())
