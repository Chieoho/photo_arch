# -*- coding: utf-8 -*-
"""
@file: presenter.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 15:15
"""
from typing import List
from photo_arch.use_cases.interfaces.presenter_if import PresenterIf
from photo_arch.use_cases.interfaces.dataset import GroupOutputData, PhotoOutputData


class ViewModel(object):
    def __init__(self):
        self.group: dict = GroupOutputData().__dict__
        self.photo: dict = PhotoOutputData().__dict__
        self.arch: List[dict] = []


class Presenter(PresenterIf):
    def __init__(self, model: ViewModel):
        self.view_model = model

    def update_group_model(self, group_info) -> bool:
        for k in self.view_model.group.keys():
            self.view_model.group[k] = str(group_info[k])
        return True

    def update_arch_model(self, group_info_list) -> bool:
        self.view_model.arch = []
        for group_info in group_info_list:
            group = GroupOutputData().__dict__
            for k in group.keys():
                group[k] = str(group_info[k])
            self.view_model.arch.append(group)
        return True
