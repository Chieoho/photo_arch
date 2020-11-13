# -*- coding: utf-8 -*-
"""
@file: controller.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 15:30
"""
from dataclasses import dataclass
from photo_arch.use_cases.interfaces.use_cases_if import GroupInputData, PhotoInputData
from photo_arch.use_cases.group_description import GroupDescription
from photo_arch.use_cases.photo_description import PhotoDescription
from photo_arch.adapters.sql.repo import Repo
from photo_arch.adapters.presenter import Presenter


@dataclass
class Controller(object):
    repo: Repo
    presenter: Presenter

    def save_group(self, group_info: GroupInputData):
        use_case = GroupDescription(self.repo, self.presenter)
        use_case.execute(group_info)

    def save_photo(self, photo_info: PhotoInputData):
        use_case = PhotoDescription(self.repo, self.presenter)
        use_case.execute(photo_info)
