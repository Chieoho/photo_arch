# -*- coding: utf-8 -*-
"""
@file: utils.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:02
"""
import functools
import traceback
from photo_arch.infrastructures.user_interface.qt.ui import slot_wrapper


def static(method):
    return slot_wrapper.static_(method)


def catch_exception(func):
    @functools.wraps(func)
    def wrapper(*args):
        try:
            return func(*args)
        except Exception as e:
            _ = e
            print(traceback.format_exc())
    return wrapper
