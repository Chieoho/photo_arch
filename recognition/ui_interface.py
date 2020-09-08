# -*- coding: utf-8 -*-
"""
@file: ui_interface.py
@desc:
@author: Jaden Wu
@time: 2020/8/25 10:27
"""
from abc import ABCMeta, abstractmethod


class UiInterface(metaclass=ABCMeta):
    @abstractmethod
    def start(self, params: dict) -> dict:
        """
        开始运行
        :param params: 识别参数 {"threshold": 0.8, "distance": 1}
        :return: {"res": True, "msg": "xxx"}
        """

    @abstractmethod
    def pause(self) -> dict:
        """
        暂停
        :return: {"res": True, "msg": "xxx"}
        """

    @abstractmethod
    def continue_run(self) -> dict:
        """
        继续运行
        :return: {"res": True, "msg": "xxx"}
        """

    @abstractmethod
    def get_recognition_info(self) -> dict:
        """
        获取整体识别率、已识别图片等识别信息，
        :return: {"recognition_rate": 90, "recognized_pic_num": 1000, ...}
        """

    @abstractmethod
    def get_pics_info(self, pic_type: int) -> list:
        """
        获取所有图片或部分识别图片或未识别图片的信息，
        :param pic_type: 图片类型，1代表所有图片，2代表部分识别图片，3代表未识别图片
        :return:
        [{'archival_num': '社保局-2019-0001',
          'faces': '[{"id": 0, "box": "[93, 81, 182, 192]", "name": ""}]',
          'img_path': 'D:\\深圳市社保局联谊活动\\大华\\0.jpg',
          'subject': '社保局',
          'verifyState': 0},
         {'archival_num': '社保局-2019-0001',
          'faces': '[{"id": 0, "box": "[101, 64, 174, 158]", "name": ""}]',
          'img_path': 'D:\\深圳市社保局联谊活动\\大华\\1.jpg',
          'subject': '社保局',
          'verifyState': 0}]
        """

    @abstractmethod
    def set_archival_number(self, arch_num_info: dict) -> bool:
        """
        预设档号
        :param arch_num_info: 档号信息。如：{"root": {"root_path": "1"}, "children": {"path1": "1001", "path2": "1002"}}
        :return: True or False
        """

    @abstractmethod
    def get_archival_number(self, path) -> dict:
        """
        获取档号信息
        :param path: 路径
        :return: 档号信息。如：{"root": {"root_path": "1"}, "children": {"path1": "1001", "path2": "1002"}}
        """

    @abstractmethod
    def start_training(self) -> dict:
        """
        开始训练
        :return: 返回训练后模型信息，如：{"model_acc": 0.8}
        """

    @abstractmethod
    def checked(self, checked_info: dict) -> bool:
        """
        已核验
        :param checked_info: 已核验信息  如：
        {"path": "g:\\xx", "arch_num": "A-001", "theme": "主题1",
        "faces": [{"name": "张三", "id": "001", "box": "[x, y, l, h]"}],
        "table_widget": [{"name": "张三", "id": "001"}]}
        :return: True or False
        """
