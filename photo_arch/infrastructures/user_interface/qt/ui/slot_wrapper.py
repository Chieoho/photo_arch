# -*- coding: utf-8 -*-
"""
@file: slot_wrapper.py
@desc:
@author: Jaden Wu
@time: 2020/11/24 22:00
"""
from photo_arch.infrastructures.user_interface.qt.ui import slot_wrapper


def static_(method):
    return slot_wrapper.static_(method)
