# -*- coding: utf-8 -*-
"""
@file: photo_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:46
"""
from photo_arch.use_cases.interfaces.presenter_if.photo_description import PresenterIf
from photo_arch.adapters.view_model.photo_description import ViewModel


class Presenter(PresenterIf):
    def __init__(self, model: ViewModel):
        self.view_model = model
