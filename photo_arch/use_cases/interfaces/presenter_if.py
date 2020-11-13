# -*- coding: utf-8 -*-
"""
@file: presenter_if.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 14:36
"""
from abc import ABCMeta, abstractmethod


class GroupOutputData(object):
    arch_code: str = ''
    fonds_code: str = ''
    arch_category_code: str = ''
    retention_period: str = ''
    year: str = ''
    department: str = ''
    group_code: str = ''
    group_title: str = ''
    group_caption: str = ''
    author: str = ''
    folder_size: str = ''
    photographer: str = ''
    taken_time: str = ''
    taken_locations: str = ''
    photo_num: int = 0
    security_classification: int = 0
    reference_code: str = ''
    opening_state: str = ''


class PhotoOutputData(object):
    group_arch_code: str = ''
    arch_code: str = ''
    photo_code: str = ''
    peoples: str = ''
    format: str = ''


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