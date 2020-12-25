# -*- coding: utf-8 -*-
"""
@file: data_access.py
@desc:
@author: Jaden Wu
@time: 2020/12/18 10:52
"""
from typing import List
from photo_arch.domains.photo_group import Group, Photo
from photo_arch.use_cases.interfaces.repositories_if import RepoIf
from photo_arch.adapters.sql.repo import RepoGeneral, PhotoGroupModel, PhotoModel, SettingModel


class Repo(RepoIf):
    def __init__(self, session):
        self.session = session
        self.repo_general = RepoGeneral(session)

    def __del__(self):
        self.session.close()

    def add_group(self, group: Group) -> bool:
        group_dict = group.to_dict()
        new_group = PhotoGroupModel(**group_dict)
        self.session.add(new_group)
        self.session.commit()
        return True

    def update_group(self, group: Group) -> bool:
        first_photo_md5 = group.first_photo_md5
        group_dict = group.to_dict()
        self.repo_general.update('photo_group', {'first_photo_md5': [first_photo_md5]}, group_dict)
        return True

    def query_group_by_group_arch_code(self, group_arch_code: str) -> List[dict]:
        group_list = self.repo_general.query('photo_group', cond={'arch_code': [group_arch_code]})
        return group_list

    def query_group_by_first_photo_md5(self, first_photo_md5: str) -> List[dict]:
        group_list = self.repo_general.query('photo_group', cond={'first_photo_md5': [first_photo_md5]})
        return group_list

    def query_group_by_selected(self, fonds_code, year, retention_period) -> List[dict]:
        group_list = self.repo_general.query(
            'photo_group',
            cond={
                'fonds_code': [fonds_code],
                'year': [year],
                'retention_period': [retention_period]
            }
        )
        return group_list

    def search_groups(self, title_key_list: list, year_key_list: list) -> List[dict]:
        group_list = self.repo_general.query(
            'photo_group',
            cond={
                'group_title': title_key_list,
                'year': year_key_list
            },
            ret_columns=('arch_code',)
        )
        return group_list

    def search_photos(self, title_key_list: list, people_key_list: list,
                      year_key_list: list) -> List[dict]:
        group_list = self.repo_general.query(
            'photo_group',
            cond={
                'group_title': title_key_list,
                'year': year_key_list
            },
            ret_columns=('group_code',)
        )
        photo_list = self.repo_general.query(
            'photo',
            cond={
                'peoples': people_key_list,
                'group_code': [gi['group_code'] for gi in group_list]
            },
            ret_columns=('photo_path',)
        )
        return photo_list

    def get_group_sn(self, year):
        query_obj = self.session.query(PhotoGroupModel).filter(PhotoGroupModel.year == year)
        return query_obj.count() + 1

    def get_all_groups(self) -> List[dict]:
        repo_general = RepoGeneral(self.session)
        group_list = repo_general.query('photo_group', cond={})
        return group_list

    def add_photo(self, photo: Photo):
        photo_dict = photo.to_dict()
        photo_dict.pop('group', None)  # 不存储张实体中的组实体
        new_photo = PhotoModel(**photo_dict)
        self.session.add(new_photo)
        self.session.commit()
        return True

    def query_photo_by_arch_code(self, photo_arch_code):
        photo_list = self.repo_general.query('photo', cond={'arch_code': [photo_arch_code]})
        return photo_list

    def add_setting(self, setting_info: dict) -> bool:
        new_setting = SettingModel(**setting_info)
        self.session.add(new_setting)
        self.session.commit()
        return True

    def query_setting(self):
        setting_list = self.repo_general.query('setting', cond={'setting_id': [1]})
        return setting_list

    def update_setting(self, setting_info: dict) -> bool:
        self.repo_general.update('setting', {'setting_id': [1]}, setting_info)
        return True

    def get_face_info(self, photo_arch_code) -> List[dict]:
        face_info_list = self.repo_general.query('face', cond={'photo_archival_code': [photo_arch_code]})
        return face_info_list
