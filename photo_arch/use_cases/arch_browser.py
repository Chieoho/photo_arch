# -*- coding: utf-8 -*-
"""
@file: arch_browser.py
@desc:
@author: Jaden Wu
@time: 2020/11/18 9:50
"""
from photo_arch.use_cases.interfaces.dataset import GroupOutputData
from photo_arch.use_cases.interfaces.repositories_if import RepoIf
from photo_arch.use_cases.interfaces.presenter_if.arch_browser import PresenterIf


class ArchBrowser(object):
    def __init__(self, repo: RepoIf, pres: PresenterIf):
        self.repo = repo
        self.pres = pres

    def browse_arch(self) -> bool:
        group_list = self.repo.get_all_groups()
        self.pres.update_arch_model(group_list)
        return True

    def get_group(self, group_arch_code: str) -> bool:
        group_list = self.repo.query_group_by_group_arch_code(group_arch_code)
        if group_list:
            group_info = group_list[-1]
        else:
            group_info = GroupOutputData().__dict__
        self.pres.update_group_model(group_info)
        return True
