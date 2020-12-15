# -*- coding: utf-8 -*-
"""
@file: arch_searcher.py
@desc:
@author: Jaden Wu
@time: 2020/12/10 14:44
"""
from typing import List
from abc import ABCMeta, abstractmethod


class PresenterIf(metaclass=ABCMeta):
    @abstractmethod
    def update_group_list(self, group_info_list: List[dict]):
        """
        :param group_info_list:
        :return:
        """

    @abstractmethod
    def update_photo_list(self, photo_info_list: List[dict]):
        """
        :param photo_info_list:
        :return:
        """

    @abstractmethod
    def update_group_model(self, group_info) -> bool:
        """
        :param group_info:
        :return:
        """

    @abstractmethod
    def update_photo_model(self, photo_info) -> bool:
        """
        :param photo_info:
        :return:
        """
