# -*- coding: utf-8 -*-
"""
@file: recognition.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 13:08
"""
from photo_arch.use_cases.interfaces.presenter_if.recognition import PresenterIf


class ViewModel(object):
    def __init__(self):
        pass


class Presenter(PresenterIf):
    def __init__(self):
        self.view_model = ViewModel()
