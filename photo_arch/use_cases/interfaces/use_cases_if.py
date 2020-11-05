# -*- coding: utf-8 -*-
"""
@file: use_cases_if.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 14:37
"""
from abc import ABCMeta, abstractmethod


class UseCaseIf(metaclass=ABCMeta):
    @abstractmethod
    def execute(self):
        """
        执行用例
        :return:
        """