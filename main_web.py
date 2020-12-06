# -*- coding: utf-8 -*-
"""
@file: main_web.py
@desc:
@author: Jaden Wu
@time: 2020/12/5 20:30
"""
from photo_arch.infrastructures.user_interface.restful import app


def main():
    app.run(host='127.0.0.1', port=80)


if __name__ == '__main__':
    main()
