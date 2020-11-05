# -*- coding: utf-8 -*-
"""
@file: db_setting.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 15:34
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from photo_arch.adapters.sql import create_database
from photo_arch.adapters.sql.tc_repo import Base


def init_db():
    db_username = 'root'
    db_password = '123456'
    db_ip = '192.168.66.50'
    db_port = 3306
    db_name = 'auto_test'
    # db_uri = f'mysql+pymysql://{db_username}:{db_password}@{db_ip}:{db_port}/{db_name}?charset=utf8mb4'
    db_uri = 'sqlite:///./auto_test/infrastructures/databases/auto_test.db'
    create_database(db_uri.replace(db_name, ''), db_name)  # db_uri含db名，而create_engine的url参数不含db名
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session_obj = scoped_session(session_factory)
    session = session_obj()
    return session
