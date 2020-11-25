# -*- coding: utf-8 -*-
"""
@file: arch_transfer.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 13:10
"""
from photo_arch.use_cases.interfaces.presenter_if.arch_transfer import PresenterIf
from photo_arch.adapters.view_model.arch_transfer import ViewModel


class Presenter(PresenterIf):
    def __init__(self, model: ViewModel):
        self.view_model = model
