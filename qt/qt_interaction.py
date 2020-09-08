# -*- coding: utf-8 -*-
"""
@file: qt_interaction.py
@desc:
@author: Jaden Wu
@time: 2020/9/3 10:13
"""
from recognition.ui_interface import UiInterface
import os


class QtInteraction(UiInterface):
    def start(self) -> bool:
        print('start')
        return True

    def continue_run(self) -> bool:
        print('continue')
        return True

    def pause(self) -> bool:
        print('pause')
        return True

    def get_recognition_info(self) -> dict:
        recognition_info = {
            "recognition_rate": 90,
            "recognized_face_num": 1000,
            "part_recognized_pic_num": 200,
            "all_recognized_pic_num": 300,
            "handled_pic_num": 400,
            "unhandled_pic_num": 100
        }
        return recognition_info

    def get_pics_info(self, pic_type) -> list:
        pic_info_list = [
            {'archival_num': '社保局-2019-0001',
             'faces': '[]',
             'img_path': os.path.abspath(r'.\qt\pic1.jpg'),
             'subject': '社保局主题1',
             'verifyState': 0},
            {'archival_num': '社保局-2019-0002',
             'faces': '[{"id": 1, "box": "[240, 60, 320, 140]", "name": "刘德华"}, '
                      '{"id": 2, "box": "[370, 80, 450, 160]", "name": "梅艳芳"}]',
             'img_path': os.path.abspath(r'.\qt\pic2.jpg'),
             'subject': '社保局主题2',
             'verifyState': 0},
            {'archival_num': '社保局-2019-0003',
             'faces': '[{"id": 1, "box": "[120, 60, 210, 160]", "name": "林志颖"}, '
                      '{"id": 2, "box": "[280, 100, 370, 200]", "name": "郭德纲"}]',
             'img_path': os.path.abspath(r'.\qt\pic3.jpg'),
             'subject': '社保局主题3',
             'verifyState': 0},
            {'archival_num': '社保局-2019-0004',
             'faces': '[{"id": 1, "box": "[90, 35, 210, 170]", "name": "杨幂"}, '
                      '{"id": 2, "box": "[280, 30, 400, 160]", "name": "迪丽热巴"}]',
             'img_path': os.path.abspath(r'.\qt\pic4.png'),
             'subject': '社保局主题4',
             'verifyState': 0}
        ]
        filter_dict = {
            1: [1, 1, 1, 1],
            2: [0, 1, 1, 0],
            3: [0, 1, 1, 1]
        }
        return [e for i, e in enumerate(pic_info_list) if filter_dict[pic_type][i]]

    def set_archival_number(self, arch_num_info) -> bool:
        print(arch_num_info)
        return True

    def set_training_params(self, params) -> bool:
        print(params)
        return True

    def checked(self, checked_info) -> bool:
        print(checked_info)
        return True
