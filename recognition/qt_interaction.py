# -*- coding: utf-8 -*-
"""
@file: qt_interaction.py
@desc:
@author: Jaden Wu
@time: 2020/9/3 10:14
"""
from recognition.ui_interface import UiInterface
from recognition.business_example import Recognition

__all__ = ['QtInteraction']


class QtInteraction(UiInterface):
    def __init__(self):
        self._rcn = Recognition()

    def start(self, params) -> dict:
        self._rcn.recognition()
        return {"res": True, "msg": "xxx"}

    def continue_run(self) -> dict:
        pass

    def pause(self) -> dict:
        pass

    def get_recognition_info(self) -> dict:
        pass

    def get_pics_info(self, pic_type) -> list:
        pass

    def set_archival_number(self, arch_num_info) -> bool:
        pass

    def get_archival_number(self, path) -> dict:
        pass

    def start_training(self) -> dict:
        pass

    def checked(self, checked_info) -> bool:
        pass
