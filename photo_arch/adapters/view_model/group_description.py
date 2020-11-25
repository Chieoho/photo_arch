# -*- coding: utf-8 -*-
"""
@file: group_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:41
"""
from photo_arch.use_cases.interfaces.dataset import GroupOutputData


class ViewModel(object):
    def __init__(self):
        self.group: dict = GroupOutputData().__dict__
