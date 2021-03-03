# -*- coding: utf-8 -*-
"""
@file: setting.py
@desc: 系统设置
@author: Jaden Wu
@time: 2020/11/23 9:58
"""
import os
from dataclasses import dataclass
from datetime import datetime

from PySide2 import QtWidgets, QtCore

from photo_arch.infrastructures.user_interface.qt.interaction.utils import static
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)
from license.check_license import get_lic_info, check_lic

from photo_arch.adapters.controller.setting import Controller, Repo
from photo_arch.infrastructures.databases.db_setting import session


@dataclass
class SettingData:
    fonds_name: str = ''
    fonds_code: str = ''
    description_path: str = ''
    package_path: str = ''
    license_path: str = ''
    photo_path: str = ''


class View(object):
    def __init__(self, mw_: MainWindow):
        self.ui: Ui_MainWindow = mw_.ui

    def display_setting(self, setting_data: SettingData):
        self.ui.fonds_name_in_setting.setText(setting_data.fonds_name)
        self.ui.fonds_code_in_setting.setText(setting_data.fonds_code)
        self.ui.description_path_in_setting.setText(setting_data.description_path)
        self.ui.package_path_in_setting.setText(setting_data.package_path)
        self.ui.license_path_in_setting.setText(setting_data.license_path)
        self.ui.photo_path_in_setting.setText(setting_data.photo_path)

    
@dataclass
class LicenseCtrlInfo:
    is_import: bool = False
    is_exist: bool = False
    is_valid: bool = False
    remaining_days: int = 0
    remaining_photo_num: int = 0
    enable_gpu: bool = False
    enable_export: bool = False


class Setting(object):
    def __init__(self, mw_: MainWindow):
        self.mw = mw_
        self.ui: Ui_MainWindow = mw_.ui
        self.controller = Controller(Repo(session))
        self.view = View(mw_)

        self.fonds_name = ''
        self.fonds_code = ''
        self.description_path = ''
        self.package_path = ''
        self.photo_path = ''
        self.license_path = ''
        self.lic_ctrl_info = LicenseCtrlInfo()

        self.ui.fonds_name_in_setting.textChanged.connect(static(self.save_setting))
        self.ui.fonds_code_in_setting.textChanged.connect(static(self.save_setting))
        self.ui.description_path_in_setting.textChanged.connect(static(self.save_setting))
        self.ui.package_path_in_setting.textChanged.connect(static(self.save_setting))
        self.ui.license_path_in_setting.textChanged.connect(static(self.save_setting))
        self.ui.photo_path_in_setting.textChanged.connect(static(self.save_setting))

        self.ui.select_description_dir_btn.clicked.connect(static(self.select_description_dir))
        self.ui.select_package_dir_btn.clicked.connect(static(self.select_package_dir))
        self.ui.select_photo_dir_btn.clicked.connect(static(self.select_photo_dir))
        self.ui.import_license_btn.clicked.connect(static(self.select_license))

        self._display_setting()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.display_license_info)
        self.check_license_interval = 1800 * 1000
        self.timer.start(self.check_license_interval)
        self.display_license_info()

    def _display_setting(self):
        _, setting_info = self.controller.get_setting()
        setting_data = SettingData()
        if setting_info:
            for k in setting_info:
                v = setting_info[k]
                if v:
                    setattr(self, k, setting_info[k])
                    setattr(setting_data, k, setting_info[k])
                else:
                    self.ui.tabWidget.setCurrentWidget(self.ui.setting_tab)
        else:
            self.ui.tabWidget.setCurrentWidget(self.ui.setting_tab)
        self.view.display_setting(setting_data)

    def select_description_dir(self):
        description_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self.ui.setting_tab, "选择文件夹",
            options=QtWidgets.QFileDialog.ShowDirsOnly)
        if not description_dir:
            return
        self.description_path = os.path.abspath(description_dir)
        self.ui.description_path_in_setting.setText(self.description_path)

    def select_package_dir(self):
        package_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self.ui.setting_tab, "选择文件夹",
            options=QtWidgets.QFileDialog.ShowDirsOnly)
        if not package_dir:
            return
        self.package_path = os.path.abspath(package_dir)
        self.ui.package_path_in_setting.setText(self.package_path)

    def select_photo_dir(self):
        photo_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self.ui.setting_tab, "选择文件夹",
            options=QtWidgets.QFileDialog.ShowDirsOnly)
        if not photo_dir:
            return
        self.photo_path = os.path.abspath(photo_dir)
        self.ui.photo_path_in_setting.setText(self.photo_path)

    def save_setting(self):
        setting_info = SettingData().__dict__
        for k in setting_info:
            widget = getattr(self.ui, f'{k}_in_setting')
            setting_info[k] = widget.text()
        self.__dict__.update(setting_info)
        self.controller.save_setting(setting_info)

    def display_license_info(self):
        self.lic_ctrl_info.is_import = bool(self.ui.license_path_in_setting.text())
        if self.lic_ctrl_info.is_import is False:
            self.ui.tabWidget.setCurrentWidget(self.ui.setting_tab)
            self.mw.warn_msg('未导入license，请导入有效license')
            self.timer.stop()
            return False
        self.lic_ctrl_info.is_exist = os.path.exists(self.license_path)
        if self.lic_ctrl_info.is_exist:
            lic_info = get_lic_info(self.license_path)
            self.lic_ctrl_info.is_valid = check_lic(lic_info)
            if self.lic_ctrl_info.is_valid:
                start_date = lic_info.get('start_date')
                passed_days = (datetime.now() - datetime.strptime(start_date, '%Y%m%d')).days
                used_num = self.controller.get_used_photo_num()
                max_days = lic_info.get('max_days', 0)
                max_photo_num = lic_info.get('max_photo_num', 0)
                self.lic_ctrl_info.remaining_days = max_days - passed_days
                self.lic_ctrl_info.remaining_photo_num = max_photo_num - used_num
                self.lic_ctrl_info.enable_gpu = lic_info.get('enable_gpu')
                self.lic_ctrl_info.enable_export = lic_info.get('enable_export')
                days = self.lic_ctrl_info.remaining_days
                num = self.lic_ctrl_info.remaining_photo_num
                enable_gpu = self.lic_ctrl_info.enable_gpu
                enable_export = self.lic_ctrl_info.enable_export
                self.ui.license_remaining_days.setText(f'{days if days > 0 else 0}/{max_days}')
                self.ui.license_remaining_photo_num.setText(f'{num if num > 0 else 0}/{max_photo_num}')
                self.ui.license_enable_gpu.setText('是' if enable_gpu else '否')
                self.ui.license_enable_export.setText('是' if enable_export else '否')
                self.ui.license_path_in_setting.setToolTip(self.license_path)
                over_days = self.lic_ctrl_info.remaining_days <= 0
                over_num = self.lic_ctrl_info.remaining_photo_num <= 0
                if over_days or over_num:
                    self.ui.tabWidget.setCurrentWidget(self.ui.setting_tab)
                    self.timer.stop()
                    if over_days and over_num:
                        self.mw.warn_msg('license已到期，可识别照片数量为0，请导入有效license！')
                    else:
                        if over_num:
                            self.mw.warn_msg('可识别照片数量为0，请导入有效license！')
                        else:
                            self.mw.warn_msg('license已到期，请导入有效license！')
                else:
                    return True
            else:
                self.ui.tabWidget.setCurrentWidget(self.ui.setting_tab)
                self.mw.warn_msg('license无效！请导入有效license！')
                self.timer.stop()
                return False
        else:
            self.ui.tabWidget.setCurrentWidget(self.ui.setting_tab)
            self.mw.warn_msg('license不存在！请导入有效license！')
            self.timer.stop()
            return False

    def select_license(self):
        license_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.ui.setting_tab,
            "请选择license文件", os.getcwd(), "*.cer")
        if license_path:
            self.license_path = os.path.abspath(license_path)
            self.ui.license_path_in_setting.setText(self.license_path)
            if self.display_license_info():
                if self.lic_ctrl_info.enable_gpu:
                    self.mw.info_msg('license导入成功，请重新启动软件以便使用GPU！')
                else:
                    self.mw.info_msg('license导入成功！')
                self.timer.start(self.check_license_interval)
        else:
            self.mw.warn_msg('未选择license文件')
