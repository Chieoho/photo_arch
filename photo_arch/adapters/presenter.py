# -*- coding: utf-8 -*-
"""
@file: presenter.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 15:15
"""
from photo_arch.use_cases.interfaces.presenter_if import PresenterIf


class ViewModel(object):
    def __init__(self):
        self.group_info = {

        }
        self.photo_info = {

        }


class Presenter(PresenterIf):
    def __init__(self, model: ViewModel):
        self.model = model

    def set_group_info(self, photo_info) -> bool:
        pass

    def set_photo_info(self, photo_info):
        self.model.photo_info.update(photo_info)
        return True
