# -*- coding: utf-8 -*-
"""
@file: ui_interface.py
@desc: 用户界面接口文件不应放在user_interface下，由于特殊原因，该文件由界面编写者编写和维护，
       所以放在这里。
       该接口主要完成人脸识别、张著录、模型训练和部分组著录的交互功能。
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
        :return: {"recognition_rate": 90, "recognized_photo_num": 1000, ...}
        """

    @abstractmethod
    def get_photos_info(self, photo_type: int, dir_type: int) -> list:
        """
        获取图片的信息
        :param photo_type: 图片类型，1代表所有图片，2代表部分识别图片，3代表未识别图片
        :param dir_type: 目录类型，1代表本次识别目录，2代表当前所有目录
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
    def set_arch_code(self, arch_num_info: dict) -> bool:
        """
        预设档号
        :param arch_num_info: 档号信息。如：{"root": {"root_path": "1"}, "children": {"path1": "1001", "path2": "1002"}}
        :return: True or False
        """

    @abstractmethod
    def get_arch_code(self, path) -> dict:
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
    @abstractmethod
    def get_untrained_photo_num(self) -> int:
        """
        获取未训练图片数量
        :return:
        """

    @abstractmethod
    def start_retrieve(self, file_path, dir_path) -> int:
        """
        开始检索人物
        :return:
        """

    @abstractmethod
    def get_retrieve_result(self, file_path, dir_path) -> list:
        """
         获取检索结果
         :return:
         """
