# -*- coding: utf-8 -*-
"""
@file: arch_searcher.py
@desc:
@author: Jaden Wu
@time: 2020/12/10 11:37
"""
from photo_arch.use_cases.interfaces.dataset import GroupOutputData, PhotoOutputData
from photo_arch.use_cases.interfaces.repositories_if import RepoIf
from photo_arch.use_cases.interfaces.presenter_if.arch_searcher import PresenterIf


class ArchSearcher(object):
    def __init__(self, repo: RepoIf, presenter: PresenterIf):
        self.repo = repo
        self.presenter = presenter

    def search_groups(self, title_key_list: list, year_key_list: list):
        group_info_list = self.repo.search_groups(title_key_list, year_key_list)
        self.presenter.update_group_list(group_info_list)
        return True

    def search_photos(self, title_key_list: list, people_key_list: list, year_key_list: list):
        photo_info_list = self.repo.search_photos(title_key_list, people_key_list, year_key_list)
        self.presenter.update_photo_list(photo_info_list)
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
