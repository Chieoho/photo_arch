# -*- coding: utf-8 -*-
"""
@file: test_photo_group.py
@desc:
@author: Jaden Wu
@time: 2020/11/12 9:39
"""
from photo_arch.domains.photo_group import Group, Photo


group_code = '0001'
photo_group = Group(group_code=group_code)


def test_inherit_group():
    photo = Photo(group=photo_group)
    photo.inherit_group()
    assert photo.group_code == group_code


def test_group_to_dict():
    group_dict = photo_group.to_dict()
    assert group_dict.get('group_code') == group_code


def test_photo_to_dict():
    photo = Photo(group=photo_group, photo_code='0001', arch_code='A1-ZP·2020-Y-0001-0001')
    photo_dict = photo.to_dict()
    assert photo_dict.get('photo_code') == '0001'
    assert photo_dict.get('arch_code') == 'A1-ZP·2020-Y-0001-0001'
