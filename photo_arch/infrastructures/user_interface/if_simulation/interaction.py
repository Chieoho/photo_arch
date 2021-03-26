# -*- coding: utf-8 -*-
"""
@file: interaction.py
@desc:
@author: Jaden Wu
@time: 2020/9/3 10:13
"""
import os
from pprint import pprint
import time
from photo_arch.infrastructures.user_interface.ui_interface import UiInterface

handled_photo_num = 0
unhandled_photo_num = 100


class Interaction(UiInterface):
    def __init__(self):
        self.arch_code_info = {}
        time.sleep(1)

    def start(self, params) -> dict:
        print('start')
        print(params)
        global handled_photo_num, unhandled_photo_num
        handled_photo_num = 0
        unhandled_photo_num = 100
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
        global handled_photo_num, unhandled_photo_num
        handled_photo_num += 10
        unhandled_photo_num -= 10
        recognition_info = {
            "recognition_rate": 0.9,
            "recognized_face_num": 500,
            "part_recognized_photo_num": 200,
            "all_recognized_photo_num": 300,
            "handled_photo_num": handled_photo_num,
            "unhandled_photo_num": unhandled_photo_num
        }
        return recognition_info

    def get_photos_info(self, photo_type, dir_type) -> list:
        photo_info_list = [
            {
                'arch_code': 'A2-ZP·2020-Y-0001',
                'faces': '[]',
                'arch_category_code': 'ZP',
                'fonds_code': 'A2',
                'format': 'JPGE',
                'group_code': '0001',
                'peoples': None,
                'photo_code': '0001',
                'photo_path': os.path.abspath(__file__ + '/.././photo1.jpg'),
            },
            {
                'arch_code': 'A2-ZP·2020-Y-0002',
                'arch_category_code': 'ZP',
                'fonds_code': 'A2',
                'format': 'JPGE',
                'group_code': '0001',
                'peoples': None,
                'photo_code': '0002',
                'faces': '[{"id": 1, "box": "[240, 60, 320, 140]", "name": "刘德华"}, '
                         '{"id": 2, "box": "[370, 80, 450, 160]", "name": "梅艳芳"}]',
                'photo_path': os.path.abspath(__file__ + '/.././photo2.jpg'),
            },
            {
                'arch_code': 'A2-ZP·2020-Y-0003',
                'faces': '[{"id": 1, "box": "[120, 60, 210, 160]", "name": "林志颖"}, '
                         '{"id": 2, "box": "[280, 100, 370, 200]", "name": "郭德纲"}]',
                'arch_category_code': 'ZP',
                'fonds_code': 'A2',
                'format': 'JPGE',
                'group_code': '0001',
                'peoples': None,
                'photo_code': '0003',
                'photo_path': os.path.abspath(__file__ + '/.././photo3.jpg'),
            },
            {
                'arch_code': 'A2-ZP·2020-Y-0004',
                'faces': '[{"id": 1, "box": "[90, 35, 210, 170]", "name": "杨幂"}, '
                         '{"id": 2, "box": "[280, 30, 400, 160]", "name": "迪丽热巴"}]',
                'arch_category_code': 'ZP',
                'fonds_code': 'A2',
                'format': 'JPGE',
                'group_code': '0001',
                'peoples': None,
                'photo_code': '0004',
                'photo_path': os.path.abspath(__file__ + '/.././photo4.png'),
            }
        ]
        filter_dict = {
            1: [1, 1, 1, 1],
            2: [1, 1, 0, 0],
            3: [0, 0, 1, 1]
        }
        return [e for i, e in enumerate(photo_info_list) if filter_dict[photo_type][i]]
        # return []

    def set_arch_code(self, arch_code_info) -> bool:
        pprint(arch_code_info)
        self.arch_code_info = arch_code_info
        return True

    def get_arch_code(self, path) -> dict:
        # print(path)
        if self.arch_code_info and list(self.arch_code_info.get('root').keys())[0] == path:
            return self.arch_code_info
        return {}

    def start_training(self) -> dict:
        model_info = {"model_acc": 0.9}
        return model_info

    def checked(self, checked_info) -> bool:
        pprint(checked_info)
        return True

    def get_untrained_photo_num(self) -> int:
        return 10
        # return 0

    def get_faces_coordinates(self, photo_path) -> list:
        return [{'box': [229.0, 19.0, 314.0, 77.0], 'id': 0},
                {'box': [105.0, 79.0, 162.0, 127.0], 'id': 1}]

    def start_retrieve(self, file_path, dir_path, face_list):
        pass

    def get_retrieve_result(self, file_path, dir_path):
        retrieve_results_photo_path = []
        retrieve_results_face_box = []

        retrieve_results_photo_path.append(
            os.path.abspath(r'G:\Git\photo_arch\待检索目录2\单人照\12.jpg'))
        retrieve_results_face_box.append([[142.0, 29.0, 302.0, 216.0]])

        retrieve_results_photo_path.append(
            os.path.abspath(r'G:\Git\photo_arch\待检索目录2\合照\两人照\13.png'))
        retrieve_results_face_box.append([[375.0, 10.0, 495.0, 163.0]])

        retrieve_results_photo_path.append(
            os.path.abspath(r'G:\Git\photo_arch\待检索目录2\合照\两人照\14.jpg'))
        retrieve_results_face_box.append([[248.0, 10.0, 455.0, 293.0]])

        retrieve_results_photo_path.append(
            os.path.abspath(r'G:\Git\photo_arch\待检索目录2\合照\两人照\15.jpg'))
        retrieve_results_face_box.append([[284.0, 8.0, 422.0, 168.0]])

        retrieve_results_photo_path.append(
            os.path.abspath(r'G:\Git\photo_arch\待检索目录2\合照\三人照\10.jpg'))
        retrieve_results_face_box.append([[428.0, 180.0, 695.0, 553.0]])

        retrieve_results_photo_path.append(
            os.path.abspath(r'G:\Git\photo_arch\待检索目录2\16.jpg'))
        retrieve_results_face_box.append([[229.0, 19.0, 314.0, 77.0]])

        return retrieve_results_photo_path, retrieve_results_face_box, [0]

    def get_retrieve_info(self):
        info = {
            'total_to_retrieve_photo_num': 7,
            'retrieved_photo_num': 7
        }
        return info
