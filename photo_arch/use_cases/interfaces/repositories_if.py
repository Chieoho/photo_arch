# -*- coding: utf-8 -*-
"""
@file: repositories_if.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 14:36
"""
from abc import ABCMeta, abstractmethod


class PhotoRepoIf(metaclass=ABCMeta):
    @abstractmethod
    def save(self, photo_info):
        """

        :return:
        """