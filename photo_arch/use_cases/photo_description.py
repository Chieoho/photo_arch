# -*- coding: utf-8 -*-
"""
@file: photo_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 14:32
"""
from photo_arch.domains.photo_group import PhotoGroup, Photo
from photo_arch.use_cases.interfaces.dataset import PhotoInputData
from photo_arch.use_cases.interfaces.repositories_if import RepoIf
from photo_arch.use_cases.interfaces.presenter_if import PresenterIf


class PhotoDescription(object):
    def __init__(self, repo: RepoIf, pres: PresenterIf):
        self.repo = repo
        self.pres = pres

    def execute(self, input_data: PhotoInputData):
        photo_group_info = self.repo.query_group(input_data.group_arch_code)[0]
        photo_group = PhotoGroup(**photo_group_info)
        photo = Photo(photo_group)
        photo.inherit_group()
        add_res = self.repo.add_photo(photo)
        if add_res is True:
            self.pres.set_photo_info(photo)
            return True
        return False
