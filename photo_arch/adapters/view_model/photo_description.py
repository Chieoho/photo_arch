# -*- coding: utf-8 -*-
"""
@file: photo_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:42
"""
from photo_arch.use_cases.interfaces.dataset import PhotoOutputData


class ViewModel(object):
    def __init__(self):
        self.photo: dict = PhotoOutputData().__dict__
