# -*- coding: utf-8 -*-
"""
@file: repositories_if.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 14:36
"""
from abc import ABCMeta, abstractmethod
from typing import List
from photo_arch.domains.photo_group import PhotoGroup, Photo


class RepoIf(metaclass=ABCMeta):
    """
    数据存储接口
    """
    @abstractmethod
    def add_group(self, group: PhotoGroup) -> bool:
        """
        :param group:
        :return:
        """

    @abstractmethod
    def add_photo(self, photo: Photo) -> bool:
        """
        :param photo:
        :return:
        """

    @abstractmethod
    def query_group(self, arch_code: str) -> List[dict]:
        """
        :param arch_code:
        :return:
        """