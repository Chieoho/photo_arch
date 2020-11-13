# -*- coding: utf-8 -*-
"""
@file: group_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/12 13:28
"""
from photo_arch.domains.photo_group import PhotoGroup
from photo_arch.use_cases.interfaces.use_cases_if import UseCaseIf, GroupInputData
from photo_arch.use_cases.interfaces.repositories_if import RepoIf
from photo_arch.use_cases.interfaces.presenter_if import PresenterIf


class GroupDescription(UseCaseIf):
    def __init__(self, repo: RepoIf, pres: PresenterIf):
        self.repo = repo
        self.pres = pres

    def execute(self, input_data: GroupInputData):
        photo_group = PhotoGroup(**input_data.__dict__)
        add_res = self.repo.add_group(photo_group)
        if add_res is True:
            self.pres.set_group_info(photo_group)
            return True
        return False
