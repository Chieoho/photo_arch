# -*- coding: utf-8 -*-
"""
@file: utils.py
@desc:
@author: Jaden Wu
@time: 2020/11/25 10:02
"""
import functools
import traceback
import inspect
import hashlib

from xlwt import *
from PIL import Image


from photo_arch.infrastructures.user_interface.qt.ui import slot_wrapper


def make_thumb(img_path, thumb_path, sizes=(100, 100)):
    im = Image.open(img_path)
    mode = im.mode
    if mode not in ('L', 'RGB'):
        im = im.convert('RGB')

    # 切成方图，避免变形
    width, height = im.size
    if width == height:
        region = im
    else:
        if width > height:
            # h*h
            delta = (width - height) / 2
            box = (delta, 0, delta + height, height)
        else:
            # w*w
            delta = (height - width) / 2
            box = (0, delta, width, delta + width)
        region = im.crop(box)

    thumb = region.resize((sizes[0], sizes[1]), Image.ANTIALIAS)
    thumb.save(thumb_path, quality=100)


def table_widget_to_xls(table_widget, xls_path):
    sheet_qty = 65000
    column_qty = table_widget.columnCount()
    row_qty = table_widget.rowCount()
    w = Workbook()
    fnt = Font()
    fnt.height = 320
    style = XFStyle()
    style.font = fnt
    for i in range(row_qty // sheet_qty + 1):
        ws = w.add_sheet('Sheet%s' % (i + 1))
        for column in range(column_qty):
            head_item = table_widget.horizontalHeaderItem(column)  # 获得水平方向的Item对象
            ws.write(0, column, head_item.text())
            ws.col(column).width = 0x1400
        ws.row(0).set_style(style)

        start, end = sheet_qty * i, sheet_qty * (i + 1)
        end = end if end <= row_qty else row_qty
        for row in range(start, end):
            for column in range(column_qty):
                item = table_widget.item(row, column)
                item_text = item.text() if item else ''
                ws.write(row - start + 1, column, item_text)
            ws.row(row - start + 1).set_style(style)
    w.save(xls_path)


def calc_md5(file_path):
    if not file_path:
        return ''
    with open(file_path, 'rb') as fr:
        file_md5_obj = hashlib.md5()
        while True:
            block = fr.read(4 * 1024 * 1024)
            if not block:
                break
            file_md5_obj.update(block)
        file_md5 = file_md5_obj.hexdigest()
        return file_md5


def extend_slot(original_slot, func):
    def new_slot(*args, **kwargs):
        original_slot(*args, **kwargs)
        func(*args, **kwargs)
    setattr(original_slot.__self__, original_slot.__name__, new_slot)


def catch_exception(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            _ = e
            print(traceback.format_exc())
    return wrapper


def for_all_methods(decorator):
    def decorate(cls):
        for fn, _ in inspect.getmembers(cls, predicate=inspect.isfunction):
            if isinstance(inspect.getattr_static(cls, fn), staticmethod):
                continue
            setattr(cls, fn, decorator(getattr(cls, fn)))
        return cls
    return decorate


def static(method):
    return slot_wrapper.static_(method)


if __name__ == '__main__':
    make_thumb(r'G:\Git\photo_arch\training_data\深圳市长陈如桂一行视察恒裕前海金融中心\0003.jpg',
               r'G:\Git\photo_arch\training_data\深圳市长陈如桂一行视察恒裕前海金融中心\0003_thumb.jpg')
