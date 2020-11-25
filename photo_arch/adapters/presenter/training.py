# -*- coding: utf-8 -*-
"""
@file: training.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 13:09
"""
from photo_arch.use_cases.interfaces.presenter_if.training import PresenterIf
from photo_arch.adapters.view_model.training import ViewModel


class Presenter(PresenterIf):
    def __init__(self, model: ViewModel):
        self.view_model = model
