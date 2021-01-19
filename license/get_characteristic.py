# -*- coding: utf-8 -*-
"""
@file: get_characteristic.py
@desc:
@author: Jaden Wu
@time: 2021/1/18 10:36
"""
import uuid


def get_mac_addr():
    return hex(uuid.getnode())


def get_characteristic():
    characteristic = {
        'mac_addr': get_mac_addr(),
    }
    return characteristic
