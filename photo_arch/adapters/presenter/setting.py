# -*- coding: utf-8 -*-
"""
@file: setting.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 13:10
"""
from photo_arch.use_cases.interfaces.presenter_if.setting import PresenterIf


class Presenter(PresenterIf):
    def __init__(self, model):
        self.view_model = model
