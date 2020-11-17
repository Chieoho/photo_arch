# -*- coding: utf-8 -*-
"""
@file: controller.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 15:30
"""
from dataclasses import dataclass
from photo_arch.use_cases.interfaces.dataset import GroupInputData, PhotoInputData
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
        use_case.save_group(group_info)

    def get_group(self, group_path: str):
        use_case = GroupDescription(self.repo, self.presenter)
        use_case.get_group(group_path)

    def save_photo(self, photo_info: PhotoInputData):
        use_case = PhotoDescription(self.repo, self.presenter)
        use_case.execute(photo_info)
