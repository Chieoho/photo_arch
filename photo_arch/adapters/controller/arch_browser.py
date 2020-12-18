# -*- coding: utf-8 -*-
"""
@file: arch_browser.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:44
"""
from photo_arch.use_cases.arch_browser import ArchBrowser
from photo_arch.adapters.sql.data_access import Repo
from photo_arch.adapters.presenter.arch_browser import Presenter


class Controller(object):
    def __init__(self, repo: Repo):
        self.presenter = Presenter()
        self.arch_browser = ArchBrowser(repo, self.presenter)

    def browse_arch(self):
        res = self.arch_browser.browse_arch()
        arch = self.presenter.view_model.arch
        return res, arch

    def get_group(self, group_arch_code: str):
        res = self.arch_browser.get_group(group_arch_code)
        group = self.presenter.view_model.group
        return res, group

    def get_photo_info(self, photo_arch_code):
        res = self.arch_browser.get_photo_info(photo_arch_code)
        photo = self.presenter.view_model.photo
        return res, photo
