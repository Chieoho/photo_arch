# -*- coding: utf-8 -*-
"""
@file: training.py
@desc:
@author: Jaden Wu
@time: 2020/11/22 15:17
"""
from photo_arch.infrastructures.user_interface.qt.interaction.utils import static
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting

from photo_arch.infrastructures.databases.db_setting import engine, make_session
from photo_arch.adapters.controller.training import Controller, Repo


class View(object):
    def __init__(self, mw_: MainWindow):
        self.mw = mw_


class Training(object):
    def __init__(self, mw_: MainWindow, setting: Setting):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.setting = setting
        self.controller = Controller(Repo(make_session(engine)))
        self.view = View(mw_)

        self.ui.train_btn.clicked.connect(static(self.start_training))
        self.ui.train_btn.setStyleSheet(self.mw.button_style_sheet)

    def start_training(self):
        training_info = self.mw.interaction.start_training()
        model_acc = training_info.get('model_acc')
        if model_acc == -1:
            self.mw.msg_box('训练数据不存在，请核验人脸信息，收集数据')
        elif model_acc == -2:
            self.mw.msg_box('数据只有一类标签，至少需要两类标签')
        else:
            self.ui.model_acc_label.setText(str(model_acc))
        untrained_photo_num = self.mw.interaction.get_untrained_photo_num()
        self.ui.untrained_num_label.setText(str(untrained_photo_num))
