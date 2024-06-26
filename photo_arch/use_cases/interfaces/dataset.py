# -*- coding: utf-8 -*-
"""
@file: dataset.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 14:37
"""
from dataclasses import dataclass


@dataclass
class GroupInputData(object):
    group_path: str = ''
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
    first_photo_md5 = ''


@dataclass
class GroupOutputData(object):
    arch_code: str = ''
    group_path: str = ''
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
    photo_num: str = ''
    security_classification: str = ''
    reference_code: str = ''
    opening_state: str = ''


@dataclass
class PhotoOutputData(object):
    arch_code: str = ''
    photo_code: str = ''
    peoples: str = ''
    format: str = ''


@dataclass
class PhotoInDescription(object):
    arch_code: str = ''
    photo_code: str = ''
    peoples: str = ''
    format: str = ''
    fonds_code: str = ''
    arch_category_code: str = ''
    year: str = ''
    group_code: str = ''
    photographer: str = ''
    taken_time: str = ''
    taken_locations: str = ''
    security_classification: str = ''
    reference_code: str = ''
