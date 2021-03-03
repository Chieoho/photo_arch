# -*- coding: utf-8 -*-
"""
@file: recognition.py
@desc: 人脸识别
@author: Jaden Wu
@time: 2020/11/23 8:55
"""
import time

from PySide2 import QtCore

from photo_arch.use_cases.interfaces.dataset import PhotoInDescription
from photo_arch.infrastructures.user_interface.qt.interaction.utils import static
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow, RecognizeState)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting


class View(object):
    def __init__(self, mw_: MainWindow):
        self.mw = mw_


class Recognition(object):
    def __init__(self, mw_: MainWindow, setting: Setting):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.setting = setting
        self.view = View(mw_)

        self.update_timer = QtCore.QTimer()
        
        self.ui.recogni_btn.clicked.connect(static(self.run))
        self.ui.pausecontinue_btn.clicked.connect(static(self.pause_or_continue))
        self.update_timer.timeout.connect(static(self.periodic_update))
        self.update_timer.start(1000)
        self.ui.recogni_btn.setEnabled(False)

    def run(self):
        if self.setting.lic_ctrl_info.remaining_photo_num <= 0:
            self.mw.warn_msg('可识别照片数量为0，请导入有效license！')
            return
        self.mw.overlay(self.ui.recognition_tab)
        if self.mw.run_state != RecognizeState.running:
            thresh = self.ui.thresh_lineEdit.text()
            size = self.ui.photo_view.size()
            params = {
                "threshold": float(thresh) if thresh else 0.9,
                "label_size": (size.width(), size.height())
            }
            result = self.mw.interaction.start(params)
            if result.get('res') is True:
                self.mw.run_state = RecognizeState.running
                self.ui.pausecontinue_btn.setText('停止')
                self.ui.run_state_label.setText('识别中...')
            else:
                self.mw.msg_box(result.get('msg'))

    def pause_or_continue(self):
        if self.mw.run_state == RecognizeState.running:
            result = self.mw.interaction.pause()
            if result.get('res'):
                self.mw.run_state = RecognizeState.pause
                self.ui.pausecontinue_btn.setText('继续')
                self.ui.run_state_label.setText("暂停")
            else:
                self.mw.msg_box(result.get('msg'))

        elif self.mw.run_state == RecognizeState.pause:
            result = self.mw.interaction.continue_run()
            if result.get('res'):
                self.mw.run_state = RecognizeState.running
                self.ui.pausecontinue_btn.setText('停止')
                self.ui.run_state_label.setText('识别中...')
            else:
                self.mw.msg_box(result.get('msg'))
        else:
            pass

    def _clear_data(self):
        self.ui.photo_view.clear()

        self.ui.radio_btn_group.setExclusive(False)
        for rb in [self.ui.all_photo_radioButton,
                   self.ui.part_recognition_radioButton,
                   self.ui.all_recognition_radioButton]:
            rb.setEnabled(True)
            rb.setChecked(False)
        self.ui.radio_btn_group.setExclusive(True)

        for k in PhotoInDescription().__dict__:
            widget = getattr(self.mw.ui, f'{k}_in_photo')
            widget.setText('')

        for row in range(self.ui.tableWidget.rowCount(), -1, -1):
            self.ui.tableWidget.removeRow(row)

        self.ui.verifycheckBox.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.ui.photo_index_label.clear()

    def periodic_update(self):
        if self.mw.run_state == RecognizeState.running:
            if self.ui.tabWidget.currentIndex() == 1:
                self_info = self.mw.interaction.get_recognition_info()
                for key, value in self_info.items():
                    label = self.mw.rcn_info_label_dict.get(key)
                    if label:
                        label.setText(str(value))
                handled_photo_num = self_info.get('handled_photo_num', 0)
                unhandled_photo_num = self_info.get('unhandled_photo_num', 1)
                step = int(handled_photo_num / (handled_photo_num + unhandled_photo_num) * 100)
                self.ui.progressBar.setValue(step)
                if step >= 100:
                    self.mw.run_state = RecognizeState.stop
                    self.ui.pausecontinue_btn.setText('停止')
                    self.ui.run_state_label.setText("完成")
                    time.sleep(1)
                    photo_info_list = self.mw.interaction.get_photos_info(
                        self.mw.photo_type,
                        self.mw.dir_type)
                    self.mw.photo_list = list(map(lambda d: d['photo_path'], photo_info_list))
                    self.mw.photo_info_dict = {d['photo_path']: d for d in photo_info_list}
                    self._clear_data()
