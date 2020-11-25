# -*- coding: utf-8 -*-
"""
@file: utils.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:02
"""
import functools
import traceback
import inspect
from photo_arch.infrastructures.user_interface.qt.ui import slot_wrapper


def catch_exception(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            _ = e
            print(traceback.format_exc())
    return wrapper


def for_all_methods(decorator):
    def decorate(cls):
        for fn, _ in inspect.getmembers(cls, predicate=inspect.isfunction):
            setattr(cls, fn, decorator(getattr(cls, fn)))
        return cls
    return decorate


def static(method):
    return slot_wrapper.static_(method)
