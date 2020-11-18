# -*- coding: utf-8 -*-
"""
@file: __init__.py
@desc:
@author: Jaden Wu
@time: 2020/11/12 9:53
"""
from typing import List
from photo_arch.use_cases.interfaces.repositories_if import RepoIf
from photo_arch.use_cases.interfaces.presenter_if import PresenterIf


class Repo(RepoIf):
    def add_group(self, group) -> bool:
        return True

    def query_group_by_path(self, group_path: str) -> List[dict]:
        return [{'group_path': 'test'}]

    def add_photo(self, photo) -> bool:
        return True

    def get_all_groups(self) -> List[dict]:
        pass


class Presenter(PresenterIf):
    def set_photo_info(self, photo_info) -> bool:
        return True

    def set_group_info(self, photo_info) -> bool:
        return True


repo = Repo()
presenter = Presenter()
