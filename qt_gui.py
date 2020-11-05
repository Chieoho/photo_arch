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
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qt.qt_ui import Ui_MainWindow


SCALE = 0.786  # 初始窗体宽高和屏幕分辨率的比例


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
            from qt.qt_interaction import QtInteraction
        else:
            from recognition.qt_interaction import QtInteraction
        self.mw_instance.interaction = QtInteraction()


class Overlay(QWidget):
    def __init__(self, parent, text, dynamic=True, max_dot_num=3):
        QWidget.__init__(self, parent)
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


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, dt_width, dt_height):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.init_recognition = InitRecognition(self)
        self.init_recognition.start()

        self.pic_list = []
        self.current_pic_id = 0
        self.pic_info_dict = {}
        self.check_state_dict = {}

        self.rcn_info_label_dict = {
            "recognition_rate": self.ui.recognition_rate_label,
            "recognized_face_num": self.ui.recognized_face_label,
            "part_recognized_pic_num": self.ui.part_recognized_pic_label,
            "all_recognized_pic_num": self.ui.all_recognized_pic_label,
            "handled_pic_num": self.ui.handled_pic_label,
            "unhandled_pic_num": self.ui.unhandled_pic_label
        }
        self.run_state = RunState.stop
        self.ui.tabWidget.currentChanged.connect(self.tab_change)
        self.ui.tabWidget.setCurrentIndex(2)
        self.ui.tabWidget.setCurrentIndex(0)

        self.dt_width = dt_width
        self.dt_height = dt_height
        self.button_style_sheet = "padding-left: {0}px;" \
                                  "padding-right:{0}px;" \
                                  "padding-top:8px; " \
                                  "padding-bottom: 8px;".format(int(30*dt_width/1920))

    @catch_exception
    def tab_change(self, tab_id):
        if tab_id == 3 and hasattr(self, 'interaction'):
            untrained_pic_num = self.interaction.get_untrained_pic_num()
            self.ui.untrained_num_label.setText(str(untrained_pic_num))

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
            size = mw.ui.pic_view.size()
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
                handled_pic_num = recognition_info.get('handled_pic_num', 0)
                unhandled_pic_num = recognition_info.get('unhandled_pic_num', 1)
                step = int(handled_pic_num / (handled_pic_num + unhandled_pic_num) * 100)
                mw.ui.progressBar.setValue(step)
                if step >= 100:
                    mw.run_state = RunState.stop
                    mw.ui.pausecontinue_btn.setText('停止')
                    mw.ui.run_state_label.setText("完成")
                    time.sleep(1)
                    pic_info_list = mw.interaction.get_pics_info(Picture.pic_type, Picture.dir_type)
                    mw.pic_list = list(map(lambda d: d['img_path'], pic_info_list))
                    mw.pic_info_dict = {d['img_path']: d for d in pic_info_list}


class Picture(object):
    pic_radio_map = {
        'all_pic_radioButton': 1,
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
    pic_type = 1
    dir_type = 1

    def __init__(self):
        mw.ui.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        mw.ui.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        mw.ui.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        mw.ui.all_pic_radioButton.toggled.connect(self.pic_choose)
        mw.ui.part_recognition_radioButton.toggled.connect(self.pic_choose)
        mw.ui.all_recognition_radioButton.toggled.connect(self.pic_choose)
        mw.ui.pre_btn.clicked.connect(self.pre_pic)
        mw.ui.next_btn.clicked.connect(self.next_pic)
        mw.ui.tableWidget.itemChanged.connect(self.table_item_changed)
        mw.ui.select_dir_radioButton.toggled.connect(self.dir_choose)
        mw.ui.select_dir_radioButton.setToolTip('显示本次识别所选目录下的图片')
        mw.ui.current_dir_radioButton.toggled.connect(self.dir_choose)
        mw.ui.current_dir_radioButton.setToolTip('显示当前工作目录下的图片')

        mw.ui.all_pic_radioButton.setEnabled(False)
        mw.ui.part_recognition_radioButton.setEnabled(False)
        mw.ui.all_recognition_radioButton.setEnabled(False)

        mw.ui.pic_view.resizeEvent = self.resize_image
        mw.ui.pic_view.setAlignment(QtCore.Qt.AlignCenter)

        mw.ui.pre_btn.setStyleSheet(mw.button_style_sheet)
        mw.ui.next_btn.setStyleSheet(mw.button_style_sheet)

    @staticmethod
    @catch_exception
    def resize_image(event):
        if not Picture.pix_map:
            return
        size = event.size()
        w, h = size.width() - 1, size.height() - 1  # wow
        pix_map = Picture.pix_map.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        mw.ui.pic_view.setPixmap(pix_map)

    @staticmethod
    @catch_exception
    def pic_choose(check_state):
        if check_state is False:
            return
        mw.ui.tabWidget.setCurrentIndex(2)
        Picture.pic_type = Picture.pic_radio_map[mw.sender().objectName()]
        pic_info_list = mw.interaction.get_pics_info(Picture.pic_type, Picture.dir_type)
        mw.pic_list = list(map(lambda d: d['img_path'], pic_info_list))
        mw.pic_info_dict = {d['img_path']: d for d in pic_info_list}
        Picture.tmp_info = {}
        mw.current_pic_id = 0
        Picture._display_recognizable()

    @staticmethod
    @catch_exception
    def dir_choose(check_state):
        if check_state is False:
            return
        dir_scope, Picture.dir_type = Picture.dir_radio_map[mw.sender().objectName()]
        mw.ui.all_pic_radioButton.setText(f'显示{dir_scope}所有图片(Alt+Q)')
        mw.ui.part_recognition_radioButton.setText(f'显示{dir_scope}部分识别图片(Alt+W)')
        mw.ui.all_recognition_radioButton.setText(f'显示{dir_scope}全部识别图片(Alt+E)')
        mw.ui.all_pic_radioButton.setShortcut('Alt+Q')
        mw.ui.part_recognition_radioButton.setShortcut('Alt+W')
        mw.ui.all_recognition_radioButton.setShortcut('Alt+E')

    @staticmethod
    @catch_exception
    def pre_pic():
        if mw.ui.tabWidget.currentIndex() != 2:
            mw.ui.tabWidget.setCurrentIndex(2)
            return
        Picture.tmp_info[mw.pic_list[mw.current_pic_id]] = mw.get_name_info()
        if mw.current_pic_id > 0:
            mw.current_pic_id -= 1
            Picture._display_recognizable()

    @staticmethod
    @catch_exception
    def next_pic():
        if mw.ui.tabWidget.currentIndex() != 2:
            mw.ui.tabWidget.setCurrentIndex(2)
            return
        Picture.tmp_info[mw.pic_list[mw.current_pic_id]] = mw.get_name_info()
        if mw.current_pic_id < len(mw.pic_list) - 1:
            mw.current_pic_id += 1
            Picture._display_recognizable()

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
        del_button = Picture._create_button('删除', Picture.del_icon_path)
        del_button.clicked.connect(lambda: Picture.delete(row))
        mw.ui.tableWidget.setCellWidget(row, 2, del_button)
        add_button = Picture._create_button('添加', Picture.add_icon_path)
        add_button.clicked.connect(Picture.add)
        mw.ui.tableWidget.insertRow(row + 1)
        for col in range(2):
            item = QTableWidgetItem('')
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            mw.ui.tableWidget.setItem(row+1, col, item)
        mw.ui.tableWidget.setCellWidget(row+1, 2, add_button)
        mw.ui.verifycheckBox.setCheckState(Qt.Unchecked)
        mw.check_state_dict[mw.pic_list[mw.current_pic_id]] = Qt.Unchecked

    @staticmethod
    @catch_exception
    def delete(row):
        mw.ui.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        mw.ui.tableWidget.removeRow(row)
        for r in range(row, mw.ui.tableWidget.rowCount() - 1):
            mw.ui.tableWidget.cellWidget(r, 2).clicked.disconnect()
            Picture._connect(mw.ui.tableWidget.cellWidget(r, 2), r)
        mw.ui.verifycheckBox.setCheckState(Qt.Unchecked)
        mw.check_state_dict[mw.pic_list[mw.current_pic_id]] = Qt.Unchecked
        mw.ui.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.CurrentChanged)

    @staticmethod
    @catch_exception
    def table_item_changed():
        mw.ui.verifycheckBox.setCheckState(Qt.Unchecked)
        mw.check_state_dict[mw.pic_list[mw.current_pic_id]] = Qt.Unchecked

    @staticmethod
    @catch_exception
    def _connect(button, row):
        button.clicked.connect(lambda: Picture.delete(row))

    @staticmethod
    @catch_exception
    def _display_recognizable():
        if not mw.pic_list:
            mw.ui.pic_view.setText('没有照片可显示')
            return
        pic_path = mw.pic_list[mw.current_pic_id]
        Picture.pix_map = QPixmap(pic_path)
        faces_data = mw.pic_info_dict.get(pic_path).get('faces')
        name_info_list, coordinate_list = Picture._conversion_data(faces_data)
        tmp_name_info_list = Picture.tmp_info.get(pic_path)
        mw.ui.tableWidget.itemChanged.disconnect()
        if tmp_name_info_list is None:
            Picture._update_table_widget(name_info_list)
        else:
            Picture._update_table_widget(tmp_name_info_list)
        mw.ui.tableWidget.itemChanged.connect(Picture.table_item_changed)
        Picture._mark_face(coordinate_list)
        mw.ui.arch_num_lineEdit.setText(mw.pic_info_dict.get(pic_path).get('archival_num'))
        pix_map = Picture.pix_map.scaled(mw.ui.pic_view.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        mw.ui.pic_view.setPixmap(pix_map)
        mw.ui.pic_index_label.setText('{}/{}'.format(mw.current_pic_id + 1, len(mw.pic_list)))
        Picture._set_verify_checkbox(pic_path)

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
            del_button = Picture._create_button('删除', Picture.del_icon_path)
            Picture._connect(del_button, row)
            mw.ui.tableWidget.setCellWidget(row, 2, del_button)
        mw.ui.tableWidget.insertRow(row+1)
        for col in range(2):
            item = QTableWidgetItem('')
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            mw.ui.tableWidget.setItem(row+1, col, item)
        add_button = Picture._create_button('添加', Picture.add_icon_path)
        add_button.clicked.connect(Picture.add)
        mw.ui.tableWidget.setCellWidget(row+1, 2, add_button)

    @staticmethod
    @catch_exception
    def _set_verify_checkbox(pic_path):
        pic_info = mw.pic_info_dict.get(pic_path)
        if pic_info:
            verify_state_code = pic_info.get('verify_state', 0)
            if verify_state_code == 1:
                original_verify_state = Qt.Checked
            else:
                original_verify_state = Qt.Unchecked
        else:
            original_verify_state = Qt.Unchecked
        current_check_state = mw.check_state_dict.get(pic_path, original_verify_state)
        if current_check_state == Qt.Checked:
            mw.ui.verifycheckBox.stateChanged.disconnect()
            mw.ui.verifycheckBox.setCheckState(Qt.Checked)
            mw.ui.verifycheckBox.stateChanged.connect(Checked.checked)
        else:
            mw.ui.verifycheckBox.setCheckState(Qt.Unchecked)

    @staticmethod
    @catch_exception
    def _mark_face(coordinate_list):
        painter = QPainter(Picture.pix_map)
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


class DirTree(object):
    current_work_path = ''
    line_edit_prefix = '__line_edit__'
    type_in_icon_path = 'icon/type_in.png'

    def __init__(self):
        height = int(mw.dt_height*30/1080)
        mw.ui.treeWidget.setStyleSheet('#treeWidget::item{height:%spx;}' % (height + 5))
        mw.ui.open_dir_btn.clicked.connect(self.display_dir)
        mw.ui.treeWidget.itemClicked.connect(self.item_click)
        mw.ui.add_folder_btn.clicked.connect(self.add_folder_item)
        mw.ui.cancel_folder_btn.clicked.connect(self.cancel_folder_item)
        mw.ui.add_folder_btn.setStyleSheet(mw.button_style_sheet)
        mw.ui.cancel_folder_btn.setStyleSheet(mw.button_style_sheet)

    @staticmethod
    @catch_exception
    def display_dir():
        current_work_path = QFileDialog.getExistingDirectory(mw.ui.treeWidget, "选择文件夹",
                                                             options=QFileDialog.ShowDirsOnly)
        if not current_work_path:
            return
        mw.ui.tabWidget.setCurrentIndex(0)
        DirTree.current_work_path = os.path.abspath(current_work_path)
        mw.ui.dir_lineEdit.setText(DirTree.current_work_path)
        overlay = Overlay(mw.ui.treeWidget, '初始化中', dynamic=True)
        overlay.show()
        while 1:
            if hasattr(mw, 'interaction'):
                break
            else:
                QApplication.processEvents()
        overlay.hide()
        arch_num_info = mw.interaction.get_archival_number(DirTree.current_work_path)
        if arch_num_info and arch_num_info.get('root'):
            DirTree._generate_tree_by_data(arch_num_info)
        else:
            DirTree._generate_tree_by_path(DirTree.current_work_path)
        DirTree._reset_state()

    @staticmethod
    @catch_exception
    def _reset_state():
        mw.ui.radio_btn_group.setExclusive(False)
        for rb in [mw.ui.all_pic_radioButton,
                   mw.ui.part_recognition_radioButton,
                   mw.ui.all_recognition_radioButton]:
            rb.setEnabled(True)
            rb.setChecked(False)
        mw.ui.radio_btn_group.setExclusive(True)

        mw.ui.recogni_btn.setEnabled(True)

        for label in mw.rcn_info_label_dict.values():
            label.clear()
        mw.ui.progressBar.setValue(0)
        mw.ui.arch_num_lineEdit.clear()
        mw.ui.pic_view.clear()
        for row in range(mw.ui.tableWidget.rowCount(), -1, -1):
            mw.ui.tableWidget.removeRow(row)
        mw.ui.pic_index_label.clear()

        mw.run_state = RunState.stop
        mw.ui.pausecontinue_btn.setText('停止')
        mw.ui.run_state_label.setText("停止")

        mw.ui.verifycheckBox.setCheckState(False)

    @staticmethod
    @catch_exception
    def item_click(item):
        if item.text(0) == DirTree.current_work_path:
            return
        if item.checkState(0) == Qt.Unchecked:
            item.setCheckState(0, Qt.Checked)
        else:
            item.setCheckState(0, Qt.Unchecked)

    @staticmethod
    @catch_exception
    def add_folder_item():
        arch_num_info = {
            "root": {},
            "children": {}
        }
        root_item = mw.ui.treeWidget.invisibleRootItem().child(0)
        if root_item is None:
            return
        root_path = root_item.text(0)
        root_line_edit = mw.ui.treeWidget.itemWidget(root_item, 1)
        root_arch_num = root_line_edit.text()
        arch_num_info["root"].update({root_path: root_arch_num})
        item_iterator = QTreeWidgetItemIterator(mw.ui.treeWidget)
        items_value = item_iterator.value()
        for i in range(items_value.childCount()):
            item = items_value.child(i)
            if item.checkState(0) == Qt.Checked:
                path = item.text(0)
                line_edit = mw.ui.treeWidget.itemWidget(item, 1)
                arch_num = line_edit.text()
                arch_num_info["children"].update({os.path.join(DirTree.current_work_path, path): arch_num})
        mw.interaction.set_archival_number(arch_num_info)
        DirTree._reset_state()

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
        root_path, root_arch_num = root_arch_info
        _, volume_name = os.path.split(root_path)
        mw.ui.treeWidget.setColumnWidth(0, int(270*mw.dt_width/1920))  # 设置列宽
        mw.ui.treeWidget.setColumnWidth(1, int(270*mw.dt_width/1920))  # 设置列宽
        mw.ui.treeWidget.clear()
        root = QTreeWidgetItem(mw.ui.treeWidget)
        root.setText(0, root_path)
        line_edit = DirTree._set_line_edit(root_path, root_arch_num)
        mw.ui.treeWidget.setItemWidget(root, 1, line_edit)
        record_btn = DirTree._gen_record_btn()
        mw.ui.treeWidget.setItemWidget(root, 2, record_btn)
        for name, arch_num in file_arch_list:
            child = QTreeWidgetItem(root)
            child.setText(0, name)
            line_edit = DirTree._set_line_edit(name, arch_num)
            mw.ui.treeWidget.setItemWidget(child, 1, line_edit)
            record_btn = DirTree._gen_record_btn()
            DirTree._connect(record_btn, root_path + '\\' + name)
            mw.ui.treeWidget.setItemWidget(child, 2, record_btn)
            child.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            child.setCheckState(0, Qt.Checked)
        mw.ui.treeWidget.expandAll()

    @staticmethod
    @catch_exception
    def _set_line_edit(name, text):
        line_edit = QLineEdit(mw.ui.treeWidget)
        line_edit.setObjectName(DirTree.line_edit_prefix + name)
        line_edit.setMaximumHeight(int(mw.dt_height*30/1080))
        line_edit.setMaximumWidth(800)
        font = QFont()
        font.setFamily("新宋体")
        font.setPointSize(14)
        line_edit.setFont(font)
        line_edit.setText(text)
        return line_edit

    @staticmethod
    @catch_exception
    def _gen_record_btn():
        record_btn = QtWidgets.QPushButton(
            QIcon(QPixmap(DirTree.type_in_icon_path)),
            '著录',
            mw.ui.treeWidget
        )
        font = QFont()
        font.setFamily("新宋体")
        font.setPointSize(14)
        record_btn.setFont(font)
        record_btn.setStyleSheet("text-align: left; padding-left: 18px;")
        record_btn.setFlat(True)
        return record_btn

    @staticmethod
    @catch_exception
    def _connect(button, path):
        button.clicked.connect(lambda: mw.ui.photo_group_path_label.setText(path))

    @staticmethod
    @catch_exception
    def _generate_tree_by_path(root_path):
        file_list = filter(lambda p: os.path.isdir(os.path.join(root_path, p)), os.listdir(root_path))
        root_arch_info = (root_path, '')
        file_arch_list = [(fp, '') for fp in file_list]
        DirTree._generate_dir_tree(root_arch_info, file_arch_list)

    @staticmethod
    @catch_exception
    def _generate_tree_by_data(arch_num_info):
        root_arch = arch_num_info['root']
        root_arch_info = list(root_arch.items())[0]
        root_path = root_arch_info[0]
        children_arch = {p: '' for p in filter(lambda p: os.path.isdir(os.path.join(root_path, p)),
                                               os.listdir(root_path))}
        children_arch.update({(fp[len(root_path)+1:], an) for fp, an in arch_num_info['children'].items()})
        arch_list = children_arch.items()
        DirTree._generate_dir_tree(root_arch_info, arch_list)


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
        untrained_pic_num = mw.interaction.get_untrained_pic_num()
        mw.ui.untrained_num_label.setText(str(untrained_pic_num))


class Checked(object):
    def __init__(self):
        mw.ui.verifycheckBox.stateChanged.connect(self.checked)

    @staticmethod
    @catch_exception
    def checked():
        if mw.ui.verifycheckBox.isChecked() and mw.pic_list:
            name_list = mw.get_name_info()
            pic_path = mw.pic_list[mw.current_pic_id]
            size = mw.ui.pic_view.size()
            checked_info = {
                "path": pic_path,
                "arch_num": mw.ui.arch_num_lineEdit.text(),
                "faces": mw.pic_info_dict.get(pic_path).get('faces'),
                "table_widget": [{'id': i, 'name': n} for i, n in name_list],
                "label_size": (size.width(), size.height())
            }
            mw.interaction.checked(checked_info)
            mw.check_state_dict[pic_path] = Qt.Checked


def init_parts():
    Recognition()
    Picture()
    DirTree()
    Training()
    Checked()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    desktop = app.desktop()
    dt_width_, dt_height_ = desktop.width(), desktop.height()
    mw = MainWindow(dt_width_, dt_height_)
    mw.resize(int(dt_width_*SCALE), int(dt_height_*SCALE))
    init_parts()
    mw.show()
    sys.exit(app.exec_())
