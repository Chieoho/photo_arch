# -*- coding: utf-8 -*-
"""
@file: recognition.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 13:08
"""
from photo_arch.use_cases.recognition import Recognition
from photo_arch.adapters.sql.repo import Repo
from photo_arch.adapters.presenter.recognition import Presenter


class Controller(object):
    def __init__(self, repo: Repo, presenter: Presenter):
        self.recognition = Recognition(repo, presenter)
