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
    def __init__(self, repo: Repo, presenter: Presenter):
        self.arch_browser = ArchBrowser(repo, presenter)

    def browse_arch(self):
        self.arch_browser.browse_arch()

    def get_group(self, group_code: str):
        self.arch_browser.get_group(group_code)
