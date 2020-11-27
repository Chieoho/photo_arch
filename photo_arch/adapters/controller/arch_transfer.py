# -*- coding: utf-8 -*-
"""
@file: arch_transfer.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 13:10
"""
from photo_arch.use_cases.arch_transfer import ArchTransfer
from photo_arch.adapters.sql.repo import Repo
from photo_arch.adapters.presenter.arch_transfer import Presenter


class Controller(object):
    def __init__(self, repo: Repo, presenter: Presenter):
        self.arch_transfer = ArchTransfer(repo, presenter)

    def list_arch(self):
        self.arch_transfer.list_arch()

    def get_selected_arch(self, fonds_code, year, retention_period):
        group_list = self.arch_transfer.get_selected_arch(fonds_code, year, retention_period)
        return group_list
