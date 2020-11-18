# -*- coding: utf-8 -*-
"""
@file: test_arch_browser.py
@desc:
@author: Jaden Wu
@time: 2020/11/18 10:13
"""
from photo_arch.use_cases.group_description import GroupDescription, GroupInputData
from tests.use_cases import repo, presenter

group_description = GroupDescription(repo, presenter)


def test_get_all_groups():
    pass
