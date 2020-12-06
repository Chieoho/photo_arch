# -*- coding: utf-8 -*-
"""
@file: arch_browser.py
@desc:
@author: Jaden Wu
@time: 2020/12/5 20:30
"""
import json
from photo_arch.infrastructures.user_interface.restful import app
from photo_arch.infrastructures.databases.db_setting import engine, make_session
from photo_arch.adapters.controller.arch_browser import Controller, Repo


controller = Controller(Repo(make_session(engine)))


@app.route('/api/arch_browser/browse_arch', methods=['GET'])
def browse_arch():
    res, data = controller.browse_arch()
    return json.dumps({'result': res, 'data': data})
