# -*- coding: utf-8 -*-
"""
@file: __init__.py
@desc:
@author: Jaden Wu
@time: 2020/12/1 21:18
"""
import importlib
from threading import Thread
import sys
from flask import Flask
from photo_arch.infrastructures.user_interface.ui_interface import UiInterface

app = Flask(__name__)


class Container:
    interaction: UiInterface = None


class InitRecognition(Thread):
    def __init__(self):
        super().__init__()

    def run(self) -> None:
        if (len(sys.argv) > 1) and (sys.argv[1] in ('-t', '--test')):
            from photo_arch.infrastructures.user_interface.if_simulation.\
                interaction import Interaction
        else:
            from recognition.qt_interaction import QtInteraction as Interaction
        Container.interaction = Interaction()


def init_modules():
    importlib.import_module('.arch_browser', __package__)
    importlib.import_module('.recognition', __package__)
