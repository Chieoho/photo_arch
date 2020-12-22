# -*- coding: utf-8 -*-
"""
@file: group_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/12 13:28
"""
from photo_arch.domains.photo_group import Group
from photo_arch.use_cases.interfaces.dataset import GroupInputData
from photo_arch.use_cases.interfaces.repositories_if import RepoIf
from photo_arch.use_cases.interfaces.presenter_if.group_description import PresenterIf


class GroupDescription(object):
    def __init__(self, repo: RepoIf, pres: PresenterIf):
        self.repo = repo
        self.pres = pres

    def add_group(self, input_data: GroupInputData) -> bool:
        group = Group(**input_data.__dict__)
        return self.repo.add_group(group)

    def update_group(self, input_data: GroupInputData) -> bool:
        group = Group(**input_data.__dict__)
        return self.repo.update_group(group)

    def get_group(self, first_photo_md5: str):
        group_list = self.repo.query_group_by_first_photo_md5(first_photo_md5)
        if group_list:
            group_info = group_list[-1]
            self.pres.update_group_model(group_info)
            return True
        else:
            return False

    def get_group_sn(self, year):
        group_sn = self.repo.get_group_sn(year)
        return group_sn
