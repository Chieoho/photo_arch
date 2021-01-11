# -*- coding: utf-8 -*-
"""
@file: arch_browser.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:57
"""
from abc import ABCMeta, abstractmethod


class PresenterIf(metaclass=ABCMeta):
    @abstractmethod
    def update_arch_model(self, group_info_list) -> bool:
        """
        :param group_info_list:
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

    @abstractmethod
    def update_photo_path_model(self, photo_info) -> bool:
        """
        :param photo_info:
        :return:
        """
