# -*- coding: utf-8 -*-
"""
@file: setting.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 13:10
"""
from photo_arch.use_cases.setting import Setting
from photo_arch.adapters.sql.repo import Repo
from photo_arch.adapters.presenter.setting import Presenter


class Controller(object):
    def __init__(self, repo: Repo, presenter: Presenter):
        self.setting = Setting(repo, presenter)
