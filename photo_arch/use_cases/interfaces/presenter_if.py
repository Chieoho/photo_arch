# -*- coding: utf-8 -*-
"""
@file: presenter_if.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 14:36
"""
from abc import ABCMeta, abstractmethod


class PresenterIf(metaclass=ABCMeta):
    @abstractmethod
    def update_group_model(self, group_info) -> bool:
        """
        :param group_info:
        :return:
        """

    @abstractmethod
    def update_arch_model(self, group_info_list) -> bool:
        """
        :param group_info_list:
        :return:
        """
