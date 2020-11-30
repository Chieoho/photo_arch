# -*- coding: utf-8 -*-
"""
@file: photo_group.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 11:20
"""
from dataclasses import dataclass


@dataclass
class PhotoGroup(object):
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
    first_photo_md5: str = ''

    def to_dict(self):
        return self.__dict__


@dataclass
class Photo(object):
    group: PhotoGroup
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
    security_classification: int = 0
    reference_code: str = ''

    def inherit_group(self):
        self.fonds_code = self.group.fonds_code
        self.group_code = self.group.group_code
        self.year = self.group.year
        self.group_code = self.group.group_code
        self.photographer = self.group.photographer
        self.taken_time = self.group.taken_time
        self.taken_locations = self.group.taken_locations
        self.security_classification = self.group.security_classification
        self.reference_code = self.group.reference_code

    def to_dict(self):
        return self.__dict__
