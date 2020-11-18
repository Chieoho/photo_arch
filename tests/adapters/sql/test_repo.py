# -*- coding: utf-8 -*-
"""
@file: test_repo.py
@desc:
@author: Jaden Wu
@time: 2020/11/6 16:05
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from photo_arch.domains.photo_group import PhotoGroup, Photo
from photo_arch.adapters.sql.repo import Repo, Base

engine = create_engine('sqlite:///test.db')
Base.metadata.create_all(engine)
session_factory = sessionmaker(bind=engine)
session_obj = scoped_session(session_factory)


def test_add_group():
    repo = Repo(session_obj())
    add_group_res = repo.add_group(PhotoGroup())
    assert add_group_res is True


def test_add_photo():
    repo = Repo(session_obj())
    add_photo_res = repo.add_photo(Photo(PhotoGroup(), peoples='张三'))
    assert add_photo_res is True


def test_get_all_groups():
    repo = Repo(session_obj())
    group_list = repo.get_all_groups()
    assert isinstance(group_list, list) is True
    assert isinstance(group_list[0], dict) is True
