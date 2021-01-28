# -*- coding: utf-8 -*-
"""
@file: get_feature_code.py
@desc:
@author: Jaden Wu
@time: 2021/1/18 10:36
"""
import uuid
import hashlib


def get_mac_addr():
    return hex(uuid.getnode())


def get_feature_code():
    mac_addr = get_mac_addr()
    feature_str = mac_addr
    feature_code = hashlib.md5(feature_str.encode()).hexdigest()
    return feature_code


if __name__ == '__main__':
    print(f'机器特征码为：{get_feature_code()}')
