# -*- coding: utf-8 -*-
"""
@file: arch_browser.py
@desc:
@author: Jaden Wu
@time: 2020/11/18 9:50
"""
from photo_arch.use_cases.interfaces.dataset import GroupOutputData, PhotoOutputData
from photo_arch.use_cases.interfaces.repositories_if import RepoIf
from photo_arch.use_cases.interfaces.presenter_if.arch_browser import PresenterIf


class ArchBrowser(object):
    def __init__(self, repo: RepoIf, presenter: PresenterIf):
        self.repo = repo
        self.presenter = presenter

    def browse_arch(self) -> bool:
        group_list = self.repo.get_all_groups()
        self.presenter.update_arch_model(group_list)
        return True

    def get_group(self, group_arch_code: str) -> bool:
        group_list = self.repo.query_group_by_group_arch_code(group_arch_code)
        if group_list:
            group_info = group_list[-1]
        else:
            group_info = GroupOutputData().__dict__
        self.presenter.update_group_model(group_info)
        return True

    def get_photo_info(self, photo_arch_code):
        photo_list = self.repo.query_photo_by_arch_code(photo_arch_code)
        if photo_list:
            photo_info = photo_list[-1]
        else:
            photo_info = PhotoOutputData().__dict__
        self.presenter.update_photo_model(photo_info)
        return True

    def get_photo_path(self, photo_arch_code):
        photo_list = self.repo.query_photo_by_arch_code(photo_arch_code)
        if photo_list:
            photo_info = photo_list[-1]
            self.presenter.update_photo_path_model(photo_info)
            return True
        return False

    def get_face_info(self, photo_arch_code):
        face_info_list = self.repo.get_face_info(photo_arch_code)
        if face_info_list:
            face_info = face_info_list[-1]
        else:
            face_info = {}
        return face_info
