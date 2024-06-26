# -*- coding: utf-8 -*-
"""
@file: group_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:43
"""
from photo_arch.use_cases.interfaces.dataset import GroupInputData
from photo_arch.use_cases.group_description import GroupDescription
from photo_arch.adapters.presenter.group_description import Presenter
from photo_arch.adapters.sql.data_access import Repo


class Controller(object):
    def __init__(self, repo: Repo):
        self.presenter = Presenter()
        self.group_description = GroupDescription(repo, self.presenter)

    def add_group(self, group_info: GroupInputData):
        res = self.group_description.add_group(group_info)
        return res

    def update_group(self, group_info: GroupInputData):
        res = self.group_description.update_group(group_info)
        return res

    def get_group(self, first_photo_md5: str):
        res = self.group_description.get_group(first_photo_md5)
        group = self.presenter.view_model.group
        data = group if res is True else {}
        return res, data

    def get_group_sn(self, year):
        group_sn = self.group_description.get_group_sn(year)
        return True, group_sn
