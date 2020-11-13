# -*- coding: utf-8 -*-
"""
@file: repositories_if.py
@desc:
@author: Jaden Wu
@time: 2020/11/5 14:36
"""
from abc import ABCMeta, abstractmethod
from typing import List, Dict, Tuple


class RepoGeneralIf(metaclass=ABCMeta):
    """
    数据存储接口
    数据表有：photo, photo_group, face
    """
    @abstractmethod
    def add(self,
            table: str,
            records: List[dict]
            ) -> bool:
        """
        往table添加一条记录
        :param table: 表名 如：photo
        :param records: 记录信息列表
        :return: 成功返回True，失败返回False
        """

    @abstractmethod
    def delete(self,
               table: str,
               cond: Dict[str, list]
               ) -> bool:
        """
        删除table中符合条件的记录
        :param table: 表名 如：photo
        :param cond: 条件  如： {"year": ["2001", "2002"], "security_classification": [1]}
                              表示年度为2001或2002且密级为1的记录
        :return: 成功返回True，失败返回False
        """

    @abstractmethod
    def query(self,
              table: str,
              cond: Dict[str, list],
              ret_columns: Tuple[str] = ()
              ) -> List[dict]:
        """
        返回table中符合条件的记录
        :param table: 表名 如：photo
        :param cond: 条件  如： {"year": ["2001", "2002"], "security_classification": [1]}
                               表示年度为2001或2002且密级为1的记录
        :param ret_columns: 指定返回列，为空时返回全部列  如：("verify_state", "recog_state")
        :return: 记录列表
        """

    @abstractmethod
    def update(self,
               table: str,
               cond: Dict[str, list],
               new_info: dict
               ) -> bool:
        """
        更新table中符合条件的记录
        :param table: 表名 如：photo
        :param cond: 条件  如： {"year": ["2001", "2002"], "security_classification": [1]}
                              表示年度为2001或2002且密级为1的记录
        :param new_info: 需更新的字段及对应值
        :return: 成功返回True，失败返回False
        """
