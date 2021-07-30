# -*- coding: utf-8 -*-
"""
@file: training.py
@desc: 模型训练
@author: Jaden Wu
@time: 2020/11/22 15:17
"""
from photo_arch.infrastructures.user_interface.qt.interaction.utils import static
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)
from photo_arch.infrastructures.user_interface.qt.interaction.setting import Setting


class View(object):
    def __init__(self, mw_: MainWindow):
        self.mw = mw_


class Training(object):
    def __init__(self, mw_: MainWindow, setting: Setting):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.setting = setting
        self.view = View(mw_)

        self.ui.train_btn.clicked.connect(static(self.start_training))

    def start_training(self):
        untrained_photo_num = int(self.ui.untrained_num_label.text())
        if untrained_photo_num == 0:
            self.mw.warn_msg('未训练照片数量为0')
            return
        training_info = self.mw.interaction.start_training()
        model_acc = training_info.get('model_acc')
        if model_acc == -1:
            self.mw.msg_box('训练数据不存在，请核验人脸信息，收集数据')
        elif model_acc == -2:
            self.mw.msg_box('训练数据太少，请继续核验人脸信息，收集数据')
        else:
            self.ui.model_acc_label.setText(str(model_acc))
        untrained_photo_num = self.mw.interaction.get_untrained_photo_num()
        self.ui.untrained_num_label.setText(str(untrained_photo_num))
