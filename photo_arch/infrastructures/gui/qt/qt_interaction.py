# -*- coding: utf-8 -*-
"""
@file: qt_interaction.py
@desc:
@author: Jaden Wu
@time: 2020/9/3 10:13
"""
import os
from pprint import pprint
import time
from photo_arch.infrastructures.gui.ui_interface import UiInterface

handled_pic_num = 0
unhandled_pic_num = 500


class QtInteraction(UiInterface):
    def __init__(self):
        self.arch_num_info = {}
        time.sleep(5)

    def start(self, params) -> dict:
        print('start')
        print(params)
        global handled_pic_num, unhandled_pic_num
        handled_pic_num = 0
        unhandled_pic_num = 500
        return {"res": True, "msg": "xxx"}
        # return {"res": False, "msg": "参数错误"}

    def continue_run(self) -> dict:
        print('continue')
        return {"res": True, "msg": "xxx"}
        # return {"res": False, "msg": "继续失败"}

    def pause(self) -> dict:
        print('pause')
        return {"res": True, "msg": "xxx"}
        # return {"res": False, "msg": "暂停失败"}

    def get_recognition_info(self) -> dict:
        global handled_pic_num, unhandled_pic_num
        handled_pic_num += 10
        unhandled_pic_num -= 10
        recognition_info = {
            "recognition_rate": 0.9,
            "recognized_face_num": 1000,
            "part_recognized_pic_num": 200,
            "all_recognized_pic_num": 300,
            "handled_pic_num": handled_pic_num,
            "unhandled_pic_num": unhandled_pic_num
        }
        return recognition_info

    def get_pics_info(self, pic_type, dir_type) -> list:
        pic_info_list = [
            {'archival_num': '社保局-2019-0001',
             'faces': '[]',
             'img_path': os.path.abspath(r'.\qt\pic1.jpg'),
             'subject': '社保局主题1',
             'verify_state': 0},
            {'archival_num': '社保局-2019-0002',
             'faces': '[{"id": 1, "box": "[240, 60, 320, 140]", "name": "刘德华"}, '
                      '{"id": 2, "box": "[370, 80, 450, 160]", "name": "梅艳芳"}]',
             'img_path': os.path.abspath(r'.\qt\pic2.jpg'),
             'subject': '社保局主题2',
             'verify_state': 0},
            {'archival_num': '社保局-2019-0003',
             'faces': '[{"id": 1, "box": "[120, 60, 210, 160]", "name": "林志颖"}, '
                      '{"id": 2, "box": "[280, 100, 370, 200]", "name": "郭德纲"}]',
             'img_path': os.path.abspath(r'.\qt\pic3.jpg'),
             'subject': '社保局主题3',
             'verify_state': 0},
            {'archival_num': '社保局-2019-0004',
             'faces': '[{"id": 1, "box": "[90, 35, 210, 170]", "name": "杨幂"}, '
                      '{"id": 2, "box": "[280, 30, 400, 160]", "name": "迪丽热巴"}]',
             'img_path': os.path.abspath(r'.\qt\pic4.png'),
             'subject': '社保局主题4',
             'verify_state': 1}
        ]
        filter_dict = {
            1: [1, 1, 1, 1],
            2: [1, 1, 0, 0],
            3: [0, 0, 1, 1]
        }
        return [e for i, e in enumerate(pic_info_list) if filter_dict[pic_type][i]]
        # return []

    def set_archival_number(self, arch_num_info) -> bool:
        pprint(arch_num_info)
        self.arch_num_info = arch_num_info
        return True

    def get_archival_number(self, path) -> dict:
        # print(path)
        if self.arch_num_info and list(self.arch_num_info.get('root').keys())[0] == path:
            return self.arch_num_info
        return {}

    def start_training(self) -> dict:
        model_info = {"model_acc": 0.9}
        return model_info

    def checked(self, checked_info) -> bool:
        pprint(checked_info)
        return True

    def get_untrained_pic_num(self) -> int:
        return 10