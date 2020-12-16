# -*- coding: utf-8 -*-
"""
@file: test_group_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/12 13:41
"""
from photo_arch.use_cases.group_description import GroupDescription, GroupInputData
from tests.use_cases import repo, presenter

group_description = GroupDescription(repo, presenter)


def test_add_group():
    save_res = group_description.add_group(GroupInputData())
    assert save_res is True


def test_get_group():
    group_input_data = GroupInputData(arch_code='A1-ZP·2018-30-0001')
    group_description.add_group(group_input_data)
    get_res = group_description.get_group('A1-ZP·2018-30-0001')
    assert get_res is True
