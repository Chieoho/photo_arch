# -*- coding: utf-8 -*-
"""
@file: controller.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 15:30
"""
from photo_arch.use_cases.interfaces.use_cases_if import UseCaseIf


class Controller(object):
    def __init__(self, use_case: UseCaseIf):
        self.use_case = use_case
