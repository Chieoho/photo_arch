# -*- coding: utf-8 -*-
"""
@file: photo_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:43
"""
from photo_arch.use_cases.photo_description import PhotoDescription
from photo_arch.adapters.sql.repo import Repo
from photo_arch.adapters.presenter.photo_description import Presenter


class Controller(object):
    def __init__(self, repo: Repo):
        self.presenter = Presenter()
        self.photo_description = PhotoDescription(repo, self.presenter)
