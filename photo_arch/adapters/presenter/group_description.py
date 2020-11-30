# -*- coding: utf-8 -*-
"""
@file: group_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:46
"""
from photo_arch.use_cases.interfaces.dataset import GroupOutputData
from photo_arch.use_cases.interfaces.presenter_if.group_description import PresenterIf


class ViewModel(object):
    def __init__(self):
        self.group: dict = GroupOutputData().__dict__


class Presenter(PresenterIf):
    def __init__(self):
        self.view_model = ViewModel()

    def update_group_model(self, group_info) -> bool:
        for k in self.view_model.group.keys():
            self.view_model.group[k] = str(group_info[k])
        return True
