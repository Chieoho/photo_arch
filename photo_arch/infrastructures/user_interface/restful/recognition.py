# -*- coding: utf-8 -*-
"""
@file: recognition.py
@desc:
@author: Jaden Wu
@time: 2020/12/6 10:43
"""
import json
from photo_arch.infrastructures.user_interface.restful import app, Container as Ct


@app.route('/api/recognition/get_recognition_info', methods=['GET'])
def get_recognition_info():
    data = Ct.interaction.get_recognition_info()
    return json.dumps({'result': True, 'data': data})
