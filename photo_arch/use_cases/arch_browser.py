# -*- coding: utf-8 -*-
"""
@file: arch_browser.py
@desc:
@author: Jaden Wu
@time: 2020/11/18 9:50
"""
from photo_arch.domains.photo_group import PhotoGroup
from photo_arch.use_cases.interfaces.dataset import GroupInputData, GroupOutputData
from photo_arch.use_cases.interfaces.repositories_if import RepoIf
from photo_arch.use_cases.interfaces.presenter_if import PresenterIf


class ArchBrowser(object):
    def __init__(self, repo: RepoIf, pres: PresenterIf):
        self.repo = repo
        self.pres = pres

    def get_all_groups(self) -> bool:
        pass
