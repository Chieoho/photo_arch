# -*- coding: utf-8 -*-
"""
@file: arch_transfer.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 13:10
"""
from copy import deepcopy
from typing import List
from photo_arch.use_cases.interfaces.dataset import GroupOutputData
from photo_arch.use_cases.interfaces.presenter_if.arch_transfer import PresenterIf


class ViewModel(object):
    def __init__(self):
        self.group: dict = GroupOutputData().__dict__
        self.arch: List[GroupOutputData().__dict__] = []


class Presenter(PresenterIf):
    def __init__(self):
        self.view_model = ViewModel()

    def update_arch_vm(self, group_info_list):
        self.view_model.arch.clear()
        for group_info in group_info_list:
            group = deepcopy(self.view_model.group)
            for k in group.keys():
                group[k] = str(group_info[k])
            self.view_model.arch.append(group)
        return True
