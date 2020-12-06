# -*- coding: utf-8 -*-
"""
@file: __init__.py
@desc:
@author: Jaden Wu
@time: 2020/12/1 21:18
"""
import importlib
from flask import Flask

app = Flask(__name__)
importlib.import_module('.arch_browser', __package__)
