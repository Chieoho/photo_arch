# -*- coding: utf-8 -*-
"""
@file: self.py
@desc:
@author: Jaden Wu
@time: 2020/11/23 8:55
"""
import time
from PyQt5 import QtCore
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, View,
    RecognizeState,
    static, catch_exception
)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting


class Recognition(object):
    def __init__(self, mw_: MainWindow, setting: Setting, view: View):
        self.mw = mw_
        self.setting = setting
        self.view = view

        self.update_timer = QtCore.QTimer()
        
        self.mw.ui.recogni_btn.clicked.connect(static(self.run))
        self.mw.ui.pausecontinue_btn.clicked.connect(static(self.pause_or_continue))
        self.update_timer.timeout.connect(static(self.periodic_update))
        self.update_timer.start(1000)
        self.mw.ui.recogni_btn.setEnabled(False)
        self.mw.ui.recogni_btn.setStyleSheet(self.mw.button_style_sheet)
        self.mw.ui.pausecontinue_btn.setStyleSheet(self.mw.button_style_sheet)

    @catch_exception
    def run(self):
        if self.mw.run_state != RecognizeState.running:
            thresh = self.mw.ui.thresh_lineEdit.text()
            size = self.mw.ui.photo_view.size()
            params = {
                "threshold": float(thresh) if thresh else 0.9,
                "label_size": (size.width(), size.height())
            }
            result = self.mw.interaction.start(params)
            if result.get('res') is True:
                self.mw.run_state = RecognizeState.running
                self.mw.ui.pausecontinue_btn.setText('停止')
                self.mw.ui.run_state_label.setText('识别中...')
            else:
                self.mw.msg_box(result.get('msg'))

    @catch_exception
    def pause_or_continue(self):
        if self.mw.run_state == RecognizeState.running:
            result = self.mw.interaction.pause()
            if result.get('res'):
                self.mw.run_state = RecognizeState.pause
                self.mw.ui.pausecontinue_btn.setText('继续')
                self.mw.ui.run_state_label.setText("暂停")
            else:
                self.mw.msg_box(result.get('msg'))

        elif self.mw.run_state == RecognizeState.pause:
            result = self.mw.interaction.continue_run()
            if result.get('res'):
                self.mw.run_state = RecognizeState.running
                self.mw.ui.pausecontinue_btn.setText('停止')
                self.mw.ui.run_state_label.setText('识别中...')
            else:
                self.mw.msg_box(result.get('msg'))
        else:
            pass

    @catch_exception
    def periodic_update(self):
        if self.mw.run_state == RecognizeState.running:
            if self.mw.ui.tabWidget.currentIndex() == 1:
                self_info = self.mw.interaction.get_recognition_info()
                for key, value in self_info.items():
                    label = self.mw.rcn_info_label_dict.get(key)
                    if label:
                        label.setText(str(value))
                handled_photo_num = self_info.get('handled_photo_num', 0)
                unhandled_photo_num = self_info.get('unhandled_photo_num', 1)
                step = int(handled_photo_num / (handled_photo_num + unhandled_photo_num) * 100)
                self.mw.ui.progressBar.setValue(step)
                if step >= 100:
                    self.mw.run_state = RecognizeState.stop
                    self.mw.ui.pausecontinue_btn.setText('停止')
                    self.mw.ui.run_state_label.setText("完成")
                    time.sleep(1)
                    photo_info_list = self.mw.interaction.get_photos_info(
                        self.mw.photo_type,
                        self.mw.dir_type
                    )
                    self.mw.photo_list = list(map(lambda d: d['photo_path'], photo_info_list))
                    self.mw.photo_info_dict = {d['photo_path']: d for d in photo_info_list}
