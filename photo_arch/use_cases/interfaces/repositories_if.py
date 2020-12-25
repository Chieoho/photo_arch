# -*- coding: utf-8 -*-
"""
@file: repositories_if.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 14:36
"""
from abc import ABCMeta, abstractmethod
from typing import List
from photo_arch.domains.photo_group import Group, Photo


class RepoIf(metaclass=ABCMeta):
    """
    数据存储接口
    """
    @abstractmethod
    def add_group(self, group: Group) -> bool:
        """
        :param group:
        :return:
        """

    @abstractmethod
    def update_group(self, group: Group) -> bool:
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
    def search_groups(self, title_key_list: list, year_key_list: list) -> List[dict]:
        """
        :param title_key_list:
        :param year_key_list:
        :return:
        """

    @abstractmethod
    def search_photos(self, title_key_list: list, people_key_list: list, year_key_list: list) -> List[dict]:
        """
        :param title_key_list:
        :param people_key_list:
        :param year_key_list:
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

    @abstractmethod
    def get_face_info(self, photo_arch_code):
        """
        获取照片人脸信息
        :param photo_arch_code:
        :return:
        """