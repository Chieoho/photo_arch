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

    def query_group(self, arch_code: str) -> List[dict]:
        return [{'group_code': '0001'}]

    def add_photo(self, photo) -> bool:
        return True


class Presenter(PresenterIf):
    def set_photo_info(self, photo_info) -> bool:
        return True

    def set_group_info(self, photo_info) -> bool:
        return True


repo = Repo()
presenter = Presenter()
