# -*- coding: utf-8 -*-
"""
@file: controller.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 15:30
"""
from dataclasses import dataclass
from photo_arch.use_cases.interfaces.dataset import GroupInputData
from photo_arch.use_cases.group_description import GroupDescription
from photo_arch.use_cases.arch_browser import ArchBrowser
from photo_arch.adapters.sql.repo import Repo
from photo_arch.adapters.presenter import Presenter


@dataclass
class Controller(object):
    def __init__(self, repo: Repo, presenter: Presenter):
        self.group_description = GroupDescription(repo, presenter)
        self.arch_browser = ArchBrowser(repo, presenter)

    def save_group(self, group_info: GroupInputData):
        self.group_description.save_group(group_info)

    def get_group(self, group_code: str):
        self.group_description.get_group(group_code)

    def browse_arch(self):
        self.arch_browser.browse_arch()
