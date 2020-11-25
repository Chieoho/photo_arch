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
from photo_arch.adapters.sql.repo import Repo


class Controller(object):
    def __init__(self, repo: Repo, presenter: Presenter):
        self.group_description = GroupDescription(repo, presenter)

    def save_group(self, group_info: GroupInputData):
        self.group_description.save_group(group_info)

    def get_group(self, group_code: str):
        self.group_description.get_group(group_code)
