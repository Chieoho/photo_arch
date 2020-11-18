# -*- coding: utf-8 -*-
"""
@file: repo.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 15:08
"""
from typing import List, Dict, Tuple
from functools import partial
from sqlalchemy import Column, Integer, String, and_, or_
from photo_arch.domains.photo_group import PhotoGroup, Photo
from photo_arch.adapters.sql import Base
from photo_arch.use_cases.interfaces.repositories_if import RepoIf
from photo_arch.use_cases.interfaces.repo_general_if import RepoGeneralIf


class PhotoGroupModel(Base):
    __tablename__ = 'photo_group'
    group_id = Column(Integer, primary_key=True)
    group_path = Column(String(2048))
    arch_code = Column(String(64))
    fonds_code = Column(String(64))
    arch_category_code = Column(String(64))
    retention_period = Column(String(64))
    year = Column(String(64))
    department = Column(String(64))
    group_code = Column(String(64))
    group_title = Column(String(64))
    group_caption = Column(String(8192))
    author = Column(String(64))
    folder_size = Column(String(64))
    photographer = Column(String(64))
    taken_time = Column(String(64))
    taken_locations = Column(String(64))
    photo_num = Column(Integer)
    security_classification = Column(Integer)
    reference_code = Column(String(64))
    opening_state = Column(String(64))


class PhotoModel(Base):
    __tablename__ = 'photo'
    photo_id = Column(Integer, primary_key=True)
    photo_path = Column(String(2048))
    arch_code = Column(String(64))
    photo_code = Column(String(64))
    peoples = Column(String(8192))
    format = Column(String(64))
    fonds_code = Column(String(64))
    arch_category_code = Column(String(64))
    year = Column(String(64))
    group_code = Column(String(64))
    photographer = Column(String(64))
    taken_time = Column(String(64))
    taken_locations = Column(String(64))
    security_classification = Column(Integer)
    reference_code = Column(String(64))


class FaceModel(Base):
    __tablename__ = 'face'
    face_id = Column(Integer, primary_key=True)
    photo_path = Column(String(2048))
    photo_archival_code = Column(String(64))
    faces = Column(String(64))
    recog_state = Column(Integer)
    verify_state = Column(Integer)
    parent_path = Column(String(2048))


class Repo(RepoIf):
    def __init__(self, session):
        self.session = session
        self.repo_general = RepoGeneral(session)

    def __del__(self):
        self.session.close()

    def add_group(self, group: PhotoGroup) -> bool:
        group_dict = group.to_dict()
        new_group = PhotoGroupModel(**group_dict)
        self.session.add(new_group)
        self.session.commit()
        return True

    def update_group(self, group: PhotoGroup) -> bool:
        path = group.group_path
        group_dict = group.to_dict()
        self.repo_general.update('photo_group', {'group_path': [path]}, group_dict)
        return True

    def query_group_by_path(self, group_path: str) -> List[dict]:
        group_list = self.repo_general.query('photo_group', cond={'group_path': [group_path]})
        return group_list

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


table_model_dict = {
    'photo_group': PhotoGroupModel,
    'photo': PhotoModel,
    'face': FaceModel
}


class RepoGeneral(RepoGeneralIf):
    def __init__(self, session):
        self.session = session

    def __del__(self):
        self.session.close()

    def add(self,  table: str, records: List[dict]) -> bool:
        model = table_model_dict.get(table)
        if model:
            for r in records:
                new_record = model(**r)
                self.session.add(new_record)
            self.session.commit()
            return True
        return False

    @staticmethod
    def _row2dict(query_obj, col_names):
        d = {}
        if query_obj:
            for column in query_obj.__table__.columns:
                name = column.name
                if (not col_names) or (name in col_names):
                    d[name] = getattr(query_obj, name)
        return d

    @staticmethod
    def _gen_query_condition(search_keys_dict, key_column_list):
        condition = []
        for key, column in key_column_list:
            condition.append(or_(*list(map(lambda k: column.like('%{}%'.format(k)),
                                           search_keys_dict.get(key, [])))))
        return condition

    def _query(self, model, cond):
        for v in cond.values():
            if isinstance(v, list) is False:
                raise Exception('dict value in cond should be list')
        key_column_list = [(col, getattr(model, col)) for col in cond.keys()]
        condition = self._gen_query_condition(cond, key_column_list)
        query_obj = self.session.query(model).filter(and_(*condition))
        return query_obj

    def query(self, table: str, cond: Dict[str, list],
              ret_columns: Tuple = ()) -> List[dict]:
        model = table_model_dict.get(table)
        if model:
            row2dict = partial(self._row2dict, col_names=ret_columns)
            query_obj = self._query(model, cond)
            results = list(map(row2dict, query_obj))
            return results
        return []

    def join_query(self, tables: Tuple[str, str], cond: Tuple[str, str],
                   ret_columns: List[list]) -> List[dict]:
        if len(tables) == 2:
            t1, t2 = tables
            m1 = table_model_dict.get(t1)
            m2 = table_model_dict.get(t2)
            if m1 and m2:
                k1, k2 = cond
                cl1, cl2 = ret_columns
                kl1 = [getattr(m1, k) for k in cl1]
                kl2 = [getattr(m2, k) for k in cl2]
                query_res = self.session.query(*(kl1 + kl2)).join(m2, getattr(m1, k1) == getattr(m2, k2)).all()
                results = [dict(zip(cl1+cl2, r)) for r in query_res]
                return results
        return []

    def update(self, table: str, cond: Dict[str, list], new_info: dict) -> bool:
        model = table_model_dict.get(table)
        if model:
            query_obj = self._query(model, cond)
            for r in query_obj:
                for k, v in new_info.items():
                    setattr(r, k, v)
            self.session.commit()
            return True
        return False

    def delete(self, table: str, cond: Dict[str, list]) -> bool:
        model = table_model_dict.get(table)
        if model:
            query_obj = self._query(model, cond)
            for r in query_obj:
                self.session.delete(r)
            self.session.commit()
            return True
        return False
