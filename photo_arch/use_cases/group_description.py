# -*- coding: utf-8 -*-
"""
@file: group_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/12 13:28
"""
from photo_arch.domains.photo_group import PhotoGroup
from photo_arch.use_cases.interfaces.dataset import GroupInputData, GroupOutputData
from photo_arch.use_cases.interfaces.repositories_if import RepoIf
from photo_arch.use_cases.interfaces.presenter_if import PresenterIf


class GroupDescription(object):
    def __init__(self, repo: RepoIf, pres: PresenterIf):
        self.repo = repo
        self.pres = pres

    def save_group(self, input_data: GroupInputData) -> bool:
        group = PhotoGroup(**input_data.__dict__)
        group_path = group.group_path
        group_list = self.repo.query_group_by_path(group_path)
        if group_list:
            save_res = self.repo.update_group(group)
        else:
            save_res = self.repo.add_group(group)
        return save_res

    def get_group(self, group_path: str) -> bool:
        group_list = self.repo.query_group_by_path(group_path)
        if group_list:
            group_info = group_list[-1]
        else:
            group_info = GroupOutputData().__dict__
        self.pres.set_group_info(group_info)
        return True
