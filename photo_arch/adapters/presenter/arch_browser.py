# -*- coding: utf-8 -*-
"""
@file: arch_browser.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:46
"""
from photo_arch.use_cases.interfaces.dataset import GroupOutputData
from photo_arch.use_cases.interfaces.presenter_if.arch_browser import PresenterIf


class Presenter(PresenterIf):
    def __init__(self, model):
        self.view_model = model

    def update_arch_model(self, group_info_list) -> bool:
        self.view_model.arch = []
        for group_info in group_info_list:
            group = GroupOutputData().__dict__
            for k in group.keys():
                group[k] = str(group_info[k])
            self.view_model.arch.append(group)
        return True

    def update_group_model(self, group_info) -> bool:
        for k in self.view_model.group.keys():
            self.view_model.group[k] = str(group_info[k])
        return True
