# -*- coding: utf-8 -*-
"""
@file: arch_browser.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:41
"""
from typing import List
from photo_arch.use_cases.interfaces.dataset import GroupOutputData


class ViewModel(object):
    def __init__(self):
        self.group: dict = GroupOutputData().__dict__
        self.arch: List[dict] = []