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
import hashlib
from photo_arch.infrastructures.user_interface.qt.ui import slot_wrapper


def calc_md5(file_path):
    if not file_path:
        return ''
    with open(file_path, 'rb') as fr:
        file_md5_obj = hashlib.md5()
        while True:
            block = fr.read(4 * 1024 * 1024)
            if not block:
                break
            file_md5_obj.update(block)
        file_md5 = file_md5_obj.hexdigest()
        return file_md5


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
            if isinstance(inspect.getattr_static(cls, fn), staticmethod):
                continue
            setattr(cls, fn, decorator(getattr(cls, fn)))
        return cls
    return decorate


def static(method):
    return slot_wrapper.static_(method)
