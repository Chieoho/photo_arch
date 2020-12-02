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
    def update_group(self, group: PhotoGroup) -> bool:
        """
        :param group:
        :return:
        """

    @abstractmethod
    def query_group_by_group_arch_code(self, group_arch_code: str) -> List[dict]:
        """
        :param group_arch_code:
        :return:
        """

    @abstractmethod
    def query_group_by_first_photo_md5(self, first_photo_md5: str) -> List[dict]:
        """
        :param first_photo_md5:
        :return:
        """

    @abstractmethod
    def query_group_by_selected(self, fonds_code, year, retention_period) -> List[dict]:
        """
        :param fonds_code:
        :param year:
        :param retention_period:
        :return:
        """

    @abstractmethod
    def get_group_sn(self, year):
        """
        :param year:
        :return:
        """

    @abstractmethod
    def get_all_groups(self) -> List[dict]:
        """
        :return:
        """

    @abstractmethod
    def add_photo(self, photo: Photo) -> bool:
        """
        :param photo:
        :return:
        """

    @abstractmethod
    def query_photo_by_arch_code(self, photo_arch_code):
        """
        :param photo_arch_code:
        :return:
        """

    @abstractmethod
    def add_setting(self, setting_info: dict) -> bool:
        """
        :param setting_info:
        :return:
        """

    @abstractmethod
    def query_setting(self):
        """
        :return:
        """

    @abstractmethod
    def update_setting(self, setting_info: dict) -> bool:
        """
        :param setting_info:
        :return:
        """
