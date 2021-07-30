# -*- coding: utf-8 -*-
"""
@file: setting.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 13:10
"""
from photo_arch.use_cases.interfaces.repositories_if import RepoIf
from photo_arch.use_cases.interfaces.presenter_if.setting import PresenterIf


class Setting(object):
    def __init__(self, repo: RepoIf, pres: PresenterIf):
        self.repo = repo
        self.pres = pres

    def save_setting(self, setting_info):
        setting_list = self.repo.query_setting()
        if setting_list:
            save_res = self.repo.update_setting(setting_info)
        else:
            save_res = self.repo.add_setting(setting_info)
        return save_res

    def get_setting(self):
        return self.repo.query_setting()

    def get_used_photo_num(self):
        return self.repo.get_used_photo_num()

    def get_remaining_days(self):
        days_list = self.repo.query_remaining_days()
        return days_list[0] if days_list else {}

    def add_remaining_days(self, remaining_days_info: dict):
        res = self.repo.add_remaining_days(remaining_days_info)
        return res

    def update_remaining_days(self, remaining_days_info: dict):
        res = self.repo.update_remaining_days(remaining_days_info)
        return res
