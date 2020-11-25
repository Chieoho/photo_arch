# -*- coding: utf-8 -*-
"""
@file: group_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:46
"""
from photo_arch.use_cases.interfaces.presenter_if.group_description import PresenterIf
from photo_arch.adapters.view_model.group_description import ViewModel


class Presenter(PresenterIf):
    def __init__(self, model: ViewModel):
        self.view_model = model

    def update_group_model(self, group_info) -> bool:
        for k in self.view_model.group.keys():
            self.view_model.group[k] = str(group_info[k])
        return True
