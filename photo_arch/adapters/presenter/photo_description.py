# -*- coding: utf-8 -*-
"""
@file: photo_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:46
"""
from photo_arch.use_cases.interfaces.dataset import PhotoOutputData
from photo_arch.use_cases.interfaces.presenter_if.photo_description import PresenterIf


class ViewModel(object):
    def __init__(self):
        self.photo: dict = PhotoOutputData().__dict__


class Presenter(PresenterIf):
    def __init__(self):
        self.view_model = ViewModel()
