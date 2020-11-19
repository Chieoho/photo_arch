# -*- coding: utf-8 -*-
"""
@file: __init__.py
@desc:
@author: Jaden Wu
@time: 2020/11/12 9:53
"""
from typing import List


class Repo:
    @staticmethod
    def add_group(group) -> bool:
        _ = group
        return True

    @staticmethod
    def query_group_by_path(group_path) -> List[dict]:
        _ = group_path
        return [{'group_path': 'test'}]

    @staticmethod
    def add_photo(photo) -> bool:
        _ = photo
        return True

    @staticmethod
    def get_all_groups() -> List[dict]:
        return []

    @staticmethod
    def update_group(group) -> bool:
        _ = group
        return True


class Presenter:
    @staticmethod
    def update_group_model(group_info) -> bool:
        _ = group_info
        return True

    @staticmethod
    def update_arch_model(group_info_list) -> bool:
        _ = group_info_list
        return True


repo = Repo()
presenter = Presenter()
