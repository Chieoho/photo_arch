# -*- coding: utf-8 -*-
"""
@file: clear_data
@desc:
@author: Jaden Wu
@time: 2021/6/18 13:55
"""
import os
import shutil
import sys
import sqlite3
from PySide2 import QtWidgets
from qt_ui import Ui_Form


DATA_DIR = '.\\data'


class Form(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.clear_group_and_photo)
        self.ui.pushButton_2.clicked.connect(self.clear_group_photo_and_eigenvectors)

    def warn_msg(self, msg):
        QtWidgets.QMessageBox().warning(self, '提示', msg,
                                        QtWidgets.QMessageBox.Ok,
                                        QtWidgets.QMessageBox.Ok)

    def info_msg(self, msg):
        QtWidgets.QMessageBox().information(self, '提示', msg,
                                            QtWidgets.QMessageBox.Ok,
                                            QtWidgets.QMessageBox.Ok)

    def question(self, msg):
        reply = QtWidgets.QMessageBox.question(self, '清除数据', msg,
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        return True if reply == QtWidgets.QMessageBox.Yes else False

    def clear_group_and_photo(self):
        if self.question('确定清除组和张信息吗？') is False:
            return
        conn = sqlite3.connect('photo_arch.db')
        c = conn.cursor()
        c.execute("DELETE from photo;")
        c.execute("DELETE from photo_group;")
        conn.commit()
        clear_successfully = conn.total_changes
        conn.close()
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        if clear_successfully:
            self.info_msg('清除组和张信息成功！')
        else:
            self.warn_msg('组和张信息已被清除！')

    def clear_group_photo_and_eigenvectors(self):
        if self.question('确定清除组、张和特征向量吗？') is False:
            return
        conn = sqlite3.connect('photo_arch.db')
        c = conn.cursor()
        c.execute("DELETE from face;")
        c.execute("DELETE from photo;")
        c.execute("DELETE from photo_group;")
        conn.commit()
        clear_successfully = conn.total_changes
        conn.close()
        if os.path.exists(DATA_DIR):
            shutil.rmtree(DATA_DIR)
        if clear_successfully:
            self.info_msg('清除组、张和特征向量成功！')
        else:
            self.warn_msg('组、张和特征向量已被清除！')


def main():
    app = QtWidgets.QApplication(sys.argv)
    form = Form()
    form.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
