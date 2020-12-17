# -*- coding: utf-8 -*-
"""
@file: db_setting.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 15:34
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from photo_arch.adapters.sql import Base, create_database
from multiprocessing import Process


class DB(object):
    username = 'root'
    password = '123456'
    ip = '192.168.66.50'
    port = 3306
    name = 'auto_test'
    # uri = f'mysql+pymysql://{db_username}:{db_password}@{db_ip}:{db_port}/{db_name}?charset=utf8mb4'
    uri = 'sqlite:///photo_arch.db'


create_database(DB.uri.replace(DB.name, ''), DB.name)  # uri含db名，而create_engine的url参数不含db名
engine = create_engine(DB.uri)


def make_session(engine_):
    Base.metadata.create_all(engine_)
    session_factory = sessionmaker(bind=engine_)
    session_obj = scoped_session(session_factory)
    session_ = session_obj()
    return session_


session = make_session(engine)


class UpdateProcess(Process):
    def __init__(self, path):
        self.path = path
        super().__init__()

    def run(self) -> None:
        engine.dispose()

        from photo_arch.adapters.sql.repo import RepoGeneral
        repo_ = RepoGeneral(make_session(engine))
        repo_.update('face', {'photo_path': [self.path]}, {'faces': self.path})


if __name__ == '__main__':
    from photo_arch.adapters.sql.repo import RepoGeneral
    repo = RepoGeneral(make_session(engine))
    # repo.add('face', [{'verify_state': 3}])
    # print(repo.query('face', {'verify_state': [3, 4]}, ('face_id',)))
    # repo.delete('face', {'verify_state': [4]})
    # repo.update('face', {'verify_state': [3]}, {'verify_state': 4})
    # repo.add('photo', [{'photo_path': 'test'}])
    # repo.add('face', [{'photo_path': 'test1'}])
    # repo.add('face', [{'photo_path': 'test2'}])
    # repo.add('face', [{'photo_path': 'test3'}])
    # print(repo.join_query(('face', 'photo'), ('photo_path', 'photo_path'),
    #                       [['face_id', 'verify_state'], ['photo_id', 'photo_path']]))
    p1 = UpdateProcess('test1')
    p2 = UpdateProcess('test2')
    p3 = UpdateProcess('test3')
    for p in [p1, p2, p3]:
        p.start()
        p.join()
