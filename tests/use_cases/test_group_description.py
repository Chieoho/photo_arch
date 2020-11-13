# -*- coding: utf-8 -*-
"""
@file: test_group_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/12 13:41
"""
from photo_arch.use_cases.group_description import GroupDescription, GroupInputData
from tests.use_cases import repo, presenter


def test_group_description():
    photo_description = GroupDescription(repo, presenter)
    exe_res = photo_description.execute(GroupInputData())
    assert exe_res is True
