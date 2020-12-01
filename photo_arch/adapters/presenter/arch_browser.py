# -*- coding: utf-8 -*-
"""
@file: arch_browser.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:46
"""
from copy import deepcopy
from typing import List
from photo_arch.use_cases.interfaces.dataset import GroupOutputData, PhotoOutputData
from photo_arch.use_cases.interfaces.presenter_if.arch_browser import PresenterIf


class ViewModel(object):
    def __init__(self):
        self.group: dict = GroupOutputData().__dict__
        self.arch: List[dict] = []
        self.photo: dict = PhotoOutputData().__dict__


class Presenter(PresenterIf):
    def __init__(self):
        self.view_model = ViewModel()

    def update_arch_model(self, group_info_list) -> bool:
        self.view_model.arch.clear()
        for group_info in group_info_list:
            group = deepcopy(self.view_model.group)
            for k in group.keys():
                group[k] = str(group_info[k])
            self.view_model.arch.append(group)
        return True

    def update_group_model(self, group_info) -> bool:
        for k in self.view_model.group.keys():
            self.view_model.group[k] = str(group_info[k])
        return True

    def update_photo_model(self, photo_info) -> bool:
        for k in self.view_model.photo.keys():
            self.view_model.photo[k] = str(photo_info[k])
        return True
