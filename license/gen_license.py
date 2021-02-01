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
from datetime import datetime
from license.get_feature_code import get_feature_code


def control_info(start_date=None):
    if not start_date:
        start_date = datetime.strftime(datetime.now(), '%Y%m%d')
    ctrl_info = {
        'max_photo_num': 100,
        'start_date': start_date,
        'max_days': 30,
        'enable_gpu': False,
        'enable_export': True
    }
    return ctrl_info


def license_id():
    lic_id = {
        'key': '123456'
    }
    return lic_id


def gen_lic(feature_code=None, start_date=None):
    lic_info = license_id()
    if not feature_code:
        feature_code = get_feature_code()
    lic_info.update({'feature_code': feature_code})
    lic_info.update(control_info(start_date))
    message = json.dumps(lic_info).encode('utf8')
    with open('rsa_public_key.pem', 'rb') as fr:
        pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(fr.read())
        with open(f"./certificate/license_{datetime.now().strftime('%Y%m%d%H%M%S')}.cer", 'wb') as fw:
            fw.write(base64.b64encode(rsa.encrypt(message, pub_key)))


if __name__ == '__main__':
    gen_lic()
    # gen_lic(start_date='20210101')
    # gen_lic(feature_code='cf997a8cf771284343640550d1edd61e')
