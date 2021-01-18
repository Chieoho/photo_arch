# -*- coding: utf-8 -*-
"""
@file: gen_license.py
@desc:
@author: Jaden Wu
@time: 2021/1/15 10:31
"""
import uuid
import json
import base64
import rsa


info = {'mac_addr': hex(uuid.getnode())}


def gen_lic():
    message = json.dumps(info).encode('utf8')
    with open('public.pem', 'rb') as fr:
        pub_key = rsa.PublicKey.load_pkcs1(fr.read())
        with open('license.cer', 'wb') as fw:
            fw.write(base64.b64encode(rsa.encrypt(message, pub_key)))


if __name__ == '__main__':
    gen_lic()
