# -*- coding: utf-8 -*-
"""
@file: photo_repo.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 15:08
"""
from sqlalchemy import Column, Integer, String, PickleType
from photo_arch.adapters.sql import Base
from photo_arch.use_cases.interfaces.repositories_if import PhotoRepoIf


class PhotoModel(Base):
    __tablename__ = 'photo'
    photo_id = Column(Integer, primary_key=True)
    peoples = Column(String(8192))
    extension = Column(PickleType)


class PhotoRepo(PhotoRepoIf):
    def __init__(self, session):
        self.model = PhotoModel
        self.session = session

    def __del__(self):
        self.session.close()

    def save(self, photo_info: dict) -> int:
        new_photo = self.model(**photo_info)
        self.session.add(new_photo)
        self.session.commit()
        return new_photo.tc_id
