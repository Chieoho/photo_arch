# -*- coding: utf-8 -*-
"""
@file: training.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 13:09
"""
from photo_arch.use_cases.training import Training
from photo_arch.adapters.sql.repo import Repo
from photo_arch.adapters.presenter.training import Presenter


class Controller(object):
    def __init__(self, repo: Repo, presenter: Presenter):
        self.training = Training(repo, presenter)
