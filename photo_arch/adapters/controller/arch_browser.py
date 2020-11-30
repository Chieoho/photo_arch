# -*- coding: utf-8 -*-
"""
@file: arch_browser.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:44
"""
from photo_arch.use_cases.arch_browser import ArchBrowser
from photo_arch.adapters.sql.repo import Repo
from photo_arch.adapters.presenter.arch_browser import Presenter


class Controller(object):
    def __init__(self, repo: Repo):
        self.presenter = Presenter()
        self.arch_browser = ArchBrowser(repo, self.presenter)

    def browse_arch(self):
        res = self.arch_browser.browse_arch()
        arch = self.presenter.view_model.arch
        return res, arch

    def get_group(self, group_code: str):
        res = self.arch_browser.get_group(group_code)
        group = self.presenter.view_model.group
        return res, group
