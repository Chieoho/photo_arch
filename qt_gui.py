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
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qt.qt_ui import Ui_MainWindow


class RunState(object):
    stop = 0
    running = 1
    pause = 2


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.interaction = QtInteraction()

        # 运行
        self.run_state = RunState.stop
        self.ui.recogniButton.clicked.connect(self.run)
        self.ui.pausecontinueButton.clicked.connect(self.pause_or_continue)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.periodic_update)
        self.update_timer.start(2000)

        # 图片
        self.radio_map = {'all_pic_radioButton': 1,
                          'part_recognition_radioButton': 2,
                          'all_recognition_radioButton': 3}
        self.pix_map = None
        self.pic_list = []
        self.pic_info_dict = {}
        self.current_pic_id = 0
        self.ui.pic_view.setScaledContents(True)
        self.ui.all_pic_radioButton.toggled.connect(self.pic_choose)
        self.ui.part_recognition_radioButton.toggled.connect(self.pic_choose)
        self.ui.all_recognition_radioButton.toggled.connect(self.pic_choose)
        self.ui.preButton.clicked.connect(self.pre_pic)
        self.ui.nextButton.clicked.connect(self.next_pic)
        self.ui.all_pic_radioButton.setEnabled(False)
        self.ui.part_recognition_radioButton.setEnabled(False)
        self.ui.all_recognition_radioButton.setEnabled(False)

        # 目录树
        self.current_work_path = ''
        self.volume_dict = {}
        self.ui.dirpushButton.clicked.connect(self.display_dir)
        self.ui.treeWidget.itemChanged.connect(self.select_folder_item)
        self.ui.add_folder_btn.clicked.connect(self.add_folder_item)
        self.ui.cancel_folder_btn.clicked.connect(self.cancel_folder_item)

        # 参数
        self.ui.train_pushButton.clicked.connect(self.set_training_params)

        # 已核验
        self.ui.verifycheckBox.stateChanged.connect(self.checked)

    # 运行
    def run(self):
        self.ui.tabWidget.setCurrentIndex(0)
        self.ui.pausecontinueButton.setText('停止')
        self.ui.run_state_label.setText("运行中...")
        if self.run_state != RunState.running:
            self.run_state = RunState.running
            self.interaction.start()

    def pause_or_continue(self):
        self.ui.tabWidget.setCurrentIndex(0)
        if self.run_state == RunState.running:
            self.ui.pausecontinueButton.setText('继续')
            self.ui.run_state_label.setText("暂停")
            self.run_state = RunState.pause
            self.interaction.pause()
        elif self.run_state == RunState.pause:
            self.ui.pausecontinueButton.setText('停止')
            self.ui.run_state_label.setText("运行中...")
            self.run_state = RunState.running
            self.interaction.continue_run()
        else:
            pass

    def periodic_update(self):
        if self.run_state == RunState.running:
            if self.ui.tabWidget.currentIndex() == 0:
                recognition_info = self.interaction.get_recognition_info()
                rcn_info_label_dict = {
                    "recognition_rate": self.ui.recognition_rate_label,
                    "recognized_face_num": self.ui.recognized_face_label,
                    "part_recognized_pic_num": self.ui.part_recognized_pic_label,
                    "all_recognized_pic_num": self.ui.all_recognized_pic_label,
                    "handled_pic_num": self.ui.handled_pic_label,
                    "unhandled_pic_num": self.ui.unhandled_pic_label
                }
                for key, value in recognition_info.items():
                    rcn_info_label_dict[key].setText(str(value))

    # 图片显示
    def pic_choose(self):
        self.ui.tabWidget.setCurrentIndex(1)
        pic_info_list = self.interaction.get_pics_info(pic_type=self.radio_map[self.sender().objectName()])
        self.pic_list = list(map(lambda d: d['img_path'], pic_info_list))
        self.pic_info_dict = {d['img_path']: d for d in pic_info_list}
        self.current_pic_id = 0
        self.display_recognizable()

    def pre_pic(self):
        if self.current_pic_id > 0:
            self.current_pic_id -= 1
            self.display_recognizable()

    def next_pic(self):
        if self.current_pic_id < len(self.pic_list) - 1:
            self.current_pic_id += 1
            self.display_recognizable()

    def display_recognizable(self):
        pic_path = self.pic_list[self.current_pic_id]
        face_coordinates_list = json.loads(self.pic_info_dict.get(pic_path).get('faces'))
        for row in range(self.ui.tableWidget.rowCount(), -1, -1):
            self.ui.tableWidget.removeRow(row)
        self.pix_map = QPixmap(self.pic_list[self.current_pic_id])
        for row, face_info in enumerate(face_coordinates_list):
            self.ui.tableWidget.insertRow(row)
            id_ = str(face_info.get('id'))
            name = face_info.get('name')
            coordinate = json.loads(face_info.get('box'))
            for col, item in enumerate([id_, name]):
                item = QTableWidgetItem(item)
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.ui.tableWidget.setItem(row, col, item)
            self.mark_face(name, coordinate)
        self.ui.arch_num_lineEdit.setText(self.pic_info_dict.get(pic_path).get('archival_num'))
        self.ui.theme_textEdit.setText(self.pic_info_dict.get(pic_path).get('subject'))
        self.ui.pic_view.setPixmap(self.pix_map)
        self.ui.pic_index_label.setText('{}/{}'.format(self.current_pic_id + 1, len(self.pic_list)))
        self.ui.verifycheckBox.setCheckState(Qt.Unchecked)

    def mark_face(self, name, coordinate):
        x, y, l, h = coordinate
        painter = QPainter(self.pix_map)
        pen = QPen(QtCore.Qt.blue)
        painter.setPen(pen)
        pos = QPoint(x, y+h+15)
        painter.drawText(pos, name)
        pen = QPen(QtCore.Qt.red)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(x, y, l, h)

    # 目录树
    def generate_tree_data(self, root_volume_path):
        _, volume_name = os.path.split(root_volume_path)
        self.ui.treeWidget.setColumnWidth(0, 150)  # 设置列宽
        self.ui.treeWidget.clear()
        root = QTreeWidgetItem(self.ui.treeWidget)
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
        self.ui.treeWidget.expandAll()
        return volume_name

    def display_dir(self):
        self.ui.tabWidget.setCurrentIndex(2)
        current_work_path = QFileDialog.getExistingDirectory(self.ui.treeWidget, "选择文件夹",
                                                             options=QFileDialog.ShowDirsOnly)
        self.current_work_path = os.path.abspath(current_work_path)
        self.generate_tree_data(self.current_work_path)
        self.ui.all_pic_radioButton.setEnabled(True)
        self.ui.part_recognition_radioButton.setEnabled(True)
        self.ui.all_recognition_radioButton.setEnabled(True)

    def select_folder_item(self, item):
        path = item.text(0)
        self.volume_dict[path] = item.text(1)
        if (item.checkState(0) == Qt.Unchecked) and (path != self.current_work_path):
            self.volume_dict.pop(path, None)

    def cancel_folder_item(self):
        item = QTreeWidgetItemIterator(self.ui.treeWidget)
        child_count = item.value().childCount()
        for i in range(child_count):
            if item.value().child(i).checkState(0) == Qt.Checked:
                item.value().child(i).setCheckState(0, Qt.Unchecked)

    def add_folder_item(self):
        arch_num_info = {
            "root": {},
            "children": {}
        }
        for path, num in self.volume_dict.items():
            if os.sep in path:
                arch_num_info["root"].update({path: num})
            else:
                arch_num_info["children"].update({os.path.join(self.current_work_path, path): num})
        self.interaction.set_archival_number(arch_num_info)

    # 设置训练参数
    def set_training_params(self):
        training_params = {
            "threshold": self.ui.thresh_lineEdit.text(),
            "distance": self.ui.distance_lineEdit.text()
        }
        self.interaction.set_training_params(training_params)

    # 已核验
    def checked(self):
        if self.ui.verifycheckBox.isChecked():
            name_list = []
            for row in range(self.ui.tableWidget.rowCount()):
                id_ = self.ui.tableWidget.item(row, 0).text()
                name = self.ui.tableWidget.item(row, 1).text()
                name_list.append({'id': id_, 'name': name})
            pic_path = self.pic_list[self.current_pic_id]
            checked_info = {
                "path": pic_path,
                "arch_num": self.ui.arch_num_lineEdit.text(),
                "theme": self.ui.theme_textEdit.toPlainText(),
                "faces": self.pic_info_dict.get(pic_path).get('faces'),
                "table_widget": name_list
            }
            self.interaction.checked(checked_info)


if __name__ == "__main__":
    if (len(sys.argv) > 1) and (sys.argv[1] in ('-t', '--test')):
        from qt.qt_interaction import QtInteraction
    else:
        from recognition.qt_interaction import QtInteraction

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
