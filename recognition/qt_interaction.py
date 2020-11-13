# -*- coding: utf-8 -*-
"""
@file: qt_interaction.py
@desc:
@author: Jaden Wu
@time: 2020/9/3 10:14
"""
from photo_arch.infrastructures.gui.ui_interface import UiInterface
from recognition.business_recognition import Recognition

__all__ = ['QtInteraction']


class QtInteraction(UiInterface):
    def __init__(self):
        self._rcn = Recognition()

    def start(self, params) -> dict:
        threshold = params['threshold']
        if threshold == '':
            return {"res": False, "msg": "阈值不能设置为空字符串."}
        if float(threshold) < 0.9:
            return {"res": False, "msg": "阈值必须大于等于0.9."}

        ret = self._rcn.recognition(params)
        if ret == 0:
            return {"res": True, "msg": ""}
        else:
            return {"res": True, "msg": "已完成全部核验."}


    def continue_run(self) -> dict:
        self._rcn.continueRecognition()
        return {"res": True, "msg": ""}

    def pause(self) -> dict:
        self._rcn.pauseRecognition()
        return {"res": True, "msg": ""}

    def get_recognition_info(self) -> dict:
        return self._rcn.updateRecognitionInfo()

    def get_pics_info(self, pic_type, dir_type) -> list:
        return  self._rcn.get_recognized_face_info(pic_type, dir_type)

    def set_archival_number(self, arch_num_info) -> bool:
        ret = self._rcn.add_folderItem(arch_num_info)
        return ret

    def get_archival_number(self, path) -> dict:
        return self._rcn.get_archival_number(path)

    def start_training(self) -> dict:
        return self._rcn.trainModel()

    def checked(self, checked_info) -> bool:
        if len(checked_info) == 0 or checked_info['path'] == '' or len(eval(checked_info['faces'])) == 0  or len(checked_info['table_widget']) == 0:
            return False
        self._rcn.checke_faces_info(checked_info)
        return True

    def get_untrained_pic_num(self) -> int:
        return self._rcn.get_untrained_pic_num()
