# -*- coding: utf-8 -*-
"""
@file: arch_transfer.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 13:10
"""
from abc import ABCMeta, abstractmethod


class PresenterIf(metaclass=ABCMeta):
    @abstractmethod
    def update_arch_vm(self, group_info_list):
        """
        填充档案的view_model
        :param group_info_list:
        :return:
        """