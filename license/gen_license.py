# -*- coding: utf-8 -*-
"""
@file: gen_license.py
@desc:
@author: Jaden Wu
@time: 2021/1/15 10:31
"""
import json
import base64
import rsa
from get_characteristic import get_characteristic


def control_info():
    ctrl_info = {
        'max_photo_num': 10 ** 1,
        'max_days': 2,
        'use_gpu': True,
        'enable_export': True
    }
    return ctrl_info


def gen_lic():
    info = get_characteristic()
    info.update(control_info())
    message = json.dumps(info).encode('utf8')
    with open('public.pem', 'rb') as fr:
        pub_key = rsa.PublicKey.load_pkcs1(fr.read())
        with open('..\\license.cer', 'wb') as fw:
            fw.write(base64.b64encode(rsa.encrypt(message, pub_key)))


if __name__ == '__main__':
    gen_lic()
