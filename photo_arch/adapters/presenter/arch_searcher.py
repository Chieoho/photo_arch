# -*- coding: utf-8 -*-
"""
@file: search_archives
@desc:
@author: Jaden Wu
@time: 2020/12/10 15:20
"""
from typing import List
from photo_arch.use_cases.interfaces.dataset import GroupOutputData, PhotoOutputData
from photo_arch.use_cases.interfaces.presenter_if.arch_searcher import PresenterIf


class ViewModel(object):
    def __init__(self):
        self.group_list: List[str] = []
        self.photo_list: List[str] = []
        self.group: dict = GroupOutputData().__dict__
        self.photo: dict = PhotoOutputData().__dict__
        self.photo_path: str = ''


class Presenter(PresenterIf):
    def __init__(self):
        self.view_model = ViewModel()

    def update_group_list(self, group_info_list: List[dict]):
        self.view_model.group_list.clear()
        for gi in group_info_list:
            self.view_model.group_list.append(gi['arch_code'])

    def update_photo_list(self, photo_info_list: List[dict]):
        self.view_model.photo_list.clear()
        for pi in photo_info_list:
            self.view_model.photo_list.append(pi['arch_code'])

    def update_group_model(self, group_info) -> bool:
        for k in self.view_model.group.keys():
            self.view_model.group[k] = str(group_info[k])
        return True

    def update_photo_model(self, photo_info) -> bool:
        for k in self.view_model.photo.keys():
            self.view_model.photo[k] = str(photo_info[k])
        return True

    def update_photo_path_model(self, photo_info) -> bool:
        self.view_model.photo_path = str(photo_info.get('photo_path', ''))
        return True
