# -*- coding: utf-8 -*-
"""
@file: use_cases_if.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 14:37
"""
from abc import ABCMeta, abstractmethod
import typing
from dataclasses import dataclass


@dataclass
class GroupInputData(object):
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


@dataclass
class PhotoInputData(object):
    group_arch_code: str = ''
    arch_code: str = ''
    photo_code: str = ''
    peoples: str = ''
    format: str = ''


class UseCaseIf(metaclass=ABCMeta):
    @abstractmethod
    def execute(self, input_data: typing.Any):
        """
        用例运行
        :param input_data:
        :return:
        """


if __name__ == '__main__':
    photo_in = PhotoInputData()
    print(photo_in.__dict__)
