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
