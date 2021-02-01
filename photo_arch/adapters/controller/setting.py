# -*- coding: utf-8 -*-
"""
@file: setting.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 13:10
"""
from photo_arch.use_cases.setting import Setting
from photo_arch.adapters.sql.data_access import Repo
from photo_arch.adapters.presenter.setting import Presenter


class Controller(object):
    def __init__(self, repo: Repo):
        self.presenter = Presenter()
        self.setting = Setting(repo, self.presenter)

    def save_setting(self, setting_info):
        res = self.setting.save_setting(setting_info)
        return res

    def get_setting(self):
        setting_list = self.setting.get_setting()
        return True, setting_list[0] if setting_list else {}

    def get_used_photo_num(self):
        used_photo_num = self.setting.get_used_photo_num()
        return used_photo_num
