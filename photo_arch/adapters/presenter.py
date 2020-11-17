# -*- coding: utf-8 -*-
"""
@file: presenter.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 15:15
"""
from photo_arch.use_cases.interfaces.presenter_if import PresenterIf
from photo_arch.use_cases.interfaces.dataset import GroupOutputData, PhotoOutputData


class ViewModel(object):
    def __init__(self):
        self.group_info = GroupOutputData().__dict__
        self.photo_info = PhotoOutputData().__dict__


class Presenter(PresenterIf):
    def __init__(self, model: ViewModel):
        self.view_model = model

    def set_group_info(self, group_info) -> bool:
        group_info.pop('group_id', None)
        for k in self.view_model.group_info.keys():
            self.view_model.group_info[k] = str(group_info[k])
        return True

    def set_photo_info(self, photo_info) -> bool:
        photo_info.pop('photo_id', None)
        self.view_model.photo_info.update(photo_info)
        return True
