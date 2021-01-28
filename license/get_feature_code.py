# -*- coding: utf-8 -*-
"""
@file: get_feature_code.py
@desc:
@author: Jaden Wu
@time: 2021/1/18 10:36
"""
import uuid
import hashlib
import subprocess
import re


def get_mac_addr():
    return hex(uuid.getnode())


def run_cmd(cmd):
    out_bytes = subprocess.check_output(cmd)
    return out_bytes


def get_processor_id():
    cmd = 'wmic cpu get processorid'
    out_bytes = run_cmd(cmd)
    processor_id = re.split(rb'\s+', out_bytes)[1]
    return processor_id.decode('utf-8')


def get_product_id():
    cmd = 'wmic csproduct get uuid'
    out_bytes = run_cmd(cmd)
    product_id = re.split(rb'\s+', out_bytes)[1]
    return product_id.decode('utf-8')


def get_driver_sn():
    cmd = 'wmic diskdrive get serialnumber'
    out_bytes = run_cmd(cmd)
    driver_sn = re.split(rb'\s+', out_bytes)[1]
    return driver_sn.decode('utf-8')


def get_feature_code():
    mac_addr = get_mac_addr()
    processor_id = get_processor_id()
    product_id = get_product_id()
    driver_sn = get_driver_sn()
    feature_str = mac_addr + processor_id + product_id + driver_sn
    feature_code = hashlib.md5(feature_str.encode()).hexdigest()
    return feature_code


if __name__ == '__main__':
    print(f'机器特征码为：{get_feature_code()}')
    # print(get_processor_id())
    # print(get_product_id())
    # print(get_driver_sn())
