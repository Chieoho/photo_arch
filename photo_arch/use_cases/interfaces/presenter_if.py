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
    def set_group_info(self, photo_info) -> bool:
        """
        :param photo_info:
        :return:
        """

    @abstractmethod
    def set_photo_info(self, photo_info) -> bool:
        """
        :param photo_info:
        :return:
        """