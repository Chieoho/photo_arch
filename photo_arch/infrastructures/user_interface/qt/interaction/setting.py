# -*- coding: utf-8 -*-
"""
@file: setting.py
@desc: 系统设置
@author: Jaden Wu
@time: 2020/11/23 9:58
"""
import os
from dataclasses import dataclass

from PySide2 import QtWidgets

from photo_arch.infrastructures.user_interface.qt.interaction.utils import static
from photo_arch.infrastructures.user_interface.qt.interaction.main_window import (
    MainWindow, Ui_MainWindow)

from photo_arch.adapters.controller.setting import Controller, Repo
from photo_arch.infrastructures.databases.db_setting import session


class View(object):
    def __init__(self, mw_: MainWindow):
        self.ui: Ui_MainWindow = mw_.ui

    def display_setting(self, fonds_name, fonds_code, description_path, package_path):
        self.ui.fonds_name_in_setting.setText(fonds_name)
        self.ui.fonds_code_in_setting.setText(fonds_code)
        self.ui.description_path_in_setting.setText(description_path)
        self.ui.package_path_in_setting.setText(package_path)


@dataclass
class SettingData:
    fonds_name: str = ''
    fonds_code: str = ''
    description_path: str = ''
    package_path: str = ''


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

        self.ui.fonds_name_in_setting.textChanged.connect(static(self.save_setting))
        self.ui.fonds_code_in_setting.textChanged.connect(static(self.save_setting))
        self.ui.description_path_in_setting.textChanged.connect(static(self.save_setting))
        self.ui.package_path_in_setting.textChanged.connect(static(self.save_setting))
        self.ui.select_description_dir_btn.clicked.connect(static(self.select_description_dir))
        self.ui.select_package_dir_btn.clicked.connect(static(self.select_package_dir))

        self.ui.select_description_dir_btn.setStyleSheet(self.mw.button_style_sheet)
        self.ui.select_package_dir_btn.setStyleSheet(self.mw.button_style_sheet)

        self._get_setting()

    def _get_setting(self):
        _, setting_info = self.controller.get_setting()
        if setting_info:
            for k in setting_info:
                setattr(self, k, setting_info[k])
        else:
            self.ui.tabWidget.setCurrentWidget(self.ui.setting_tab)
        self.view.display_setting(
            self.fonds_name,
            self.fonds_code,
            self.description_path,
            self.package_path
        )

    def select_description_dir(self):
        description_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self.ui.setting_tab, "选择文件夹",
            options=QtWidgets.QFileDialog.ShowDirsOnly
        )
        if not description_dir:
            return
        self.description_path = os.path.abspath(description_dir)
        self.ui.description_path_in_setting.setText(self.description_path)

    def select_package_dir(self):
        package_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self.ui.setting_tab, "选择文件夹",
            options=QtWidgets.QFileDialog.ShowDirsOnly
        )
        if not package_dir:
            return
        self.package_path = os.path.abspath(package_dir)
        self.ui.package_path_in_setting.setText(self.package_path)

    def save_setting(self):
        setting_info = SettingData().__dict__
        for k in setting_info:
            widget = getattr(self.ui, f'{k}_in_setting')
            setting_info[k] = widget.text()
        self.__dict__.update(setting_info)
        self.controller.save_setting(setting_info)
