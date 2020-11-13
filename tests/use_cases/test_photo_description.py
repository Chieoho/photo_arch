# -*- coding: utf-8 -*-
"""
@file: test_photo_description.py
@desc:
@author: Jaden Wu
@time: 2020/11/12 9:53
"""
from photo_arch.use_cases.photo_description import PhotoDescription, PhotoInputData
from tests.use_cases import repo, presenter


def test_photo_description():
    photo_description = PhotoDescription(repo, presenter)
    exe_res = photo_description.execute(PhotoInputData())
    assert exe_res is True
