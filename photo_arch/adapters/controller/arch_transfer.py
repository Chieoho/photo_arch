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

    def get_group(self, year, retention_period):
        pass
