# -*- coding: utf-8 -*-
"""
@file: search_archives
@desc:
@author: Jaden Wu
@time: 2020/12/10 15:20
"""
from photo_arch.use_cases.arch_searcher import ArchSearcher
from photo_arch.adapters.sql.data_access import Repo
from photo_arch.adapters.presenter.arch_searcher import Presenter


class Controller(object):
    def __init__(self, repo: Repo):
        self.presenter = Presenter()
        self.arch_searcher = ArchSearcher(repo, self.presenter)

    def search_groups(self, title_key_list: list, year_key_list: list):
        res = self.arch_searcher.search_groups(title_key_list, year_key_list)
        arch_code_list = self.presenter.view_model.group_list
        return res, arch_code_list

    def search_photos(self, title_key_list: list, people_key_list: list, year_key_list: list):
        res = self.arch_searcher.search_photos(title_key_list, people_key_list, year_key_list)
        photo_info_list = self.presenter.view_model.photo_list
        return res, photo_info_list

    def get_group(self, group_arch_code: str):
        res = self.arch_searcher.get_group(group_arch_code)
        group = self.presenter.view_model.group
        return res, group

    def get_photo_info(self, photo_arch_code):
        res = self.arch_searcher.get_photo_info(photo_arch_code)
        photo = self.presenter.view_model.photo
        return res, photo
