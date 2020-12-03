# -*- coding: utf-8 -*-
"""
@file: arch_transfer.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 13:10
"""
from photo_arch.use_cases.interfaces.repositories_if import RepoIf
from photo_arch.use_cases.interfaces.presenter_if.arch_transfer import PresenterIf


class ArchTransfer(object):
    def __init__(self, repo: RepoIf, pres: PresenterIf):
        self.repo = repo
        self.pres = pres

    def list_arch(self):
        group_list = self.repo.get_all_groups()
        self.pres.update_arch_vm(group_list)
        return True

    def get_selected_arch(self, fonds_code, year, retention_period):
        group_list = self.repo.query_group_by_selected(fonds_code, year, retention_period)
        self.pres.update_arch_vm(group_list)
        return True

    def get_photo(self, photo_arch_code):
        photo_list = self.repo.query_photo_by_arch_code(photo_arch_code)
        return photo_list
