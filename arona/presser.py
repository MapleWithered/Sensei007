import time

import numpy as np
from . import resource as res, config
from .adb import ADB, MNT
import cv2
from . import imgops
from .imgreco import match_res


def press_res(res_path: str, wait=0.7):
    file_name = res.res_value(res_path)
    match len(file_name.split('-')):
        case 5:
            # file_name be like x1-y1-x2-y2-time.png
            x1, y1, x2, y2 = file_name.split('-')[:4]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            ADB.input_press_rect(x1, y1, x2, y2)
        case 4:
            # file_name be like x1-y1-x2-y2.png
            x1, y1, x2, y2 = file_name.split('-')
            y2 = y2.split('.')[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            ADB.input_press_rect(x1, y1, x2, y2)
        case 2:
            # file_name be like x1-y1.png
            x1, y1 = file_name.split('-')
            y1 = y1.split('.')[0]
            x1, y1 = int(x1), int(y1)
            ADB.input_press_pos(x1, y1)
    if wait:
        time.sleep(wait)


def wait_n_press_res(res_path: str, timeout=600, fore_wait=0.5, post_wait=0.5):
    count = 0
    while not match_res(res_path):
        time.sleep(0.5)
        count += 1
        if count / 2 > timeout:
            raise RuntimeError("wait_n_press_res timeout")
    time.sleep(fore_wait)
    press_res(res_path, post_wait)


def swipe_res(res_path: str):
    res_data = res.res_value(res_path).split('-')
    res_data = [int(x) for x in res_data]
    ADB.input_swipe(*res_data)


def wait_res(res_path: str, timeout=600):
    count = 0
    while not match_res(res_path):
        time.sleep(0.5)
        count += 1
        if count / 2 > timeout:
            raise RuntimeError("wait_res timeout")


def press_res_if_match(res_path: str, wait=0.7):
    if match_res(res_path):
        press_res(res_path, wait)


def zoom_out():
    dev = config.get_config("arona.yaml/device.touch.dev")

    operations = """u 0
u 1
w 40
c
d 0 576 766 0
d 1 576 1246 0
c
w 40
m 0 576 777 0
m 1 576 1234 0
c
w 40
m 0 576 789 0
m 1 576 1221 0
c
w 40
m 0 576 802 0
m 1 576 1208 0
c
w 40
m 0 576 813 0
m 1 576 1198 0
c
w 40
m 0 576 825 0
m 1 576 1185 0
c
w 40
m 0 576 838 0
m 1 576 1173 0
c
w 40
m 0 576 848 0
m 1 576 1162 0
c
w 40
m 0 576 861 0
m 1 576 1149 0
c
w 40
m 0 576 874 0
m 1 576 1137 0
c
w 40
m 0 576 886 0
m 1 576 1126 0
c
w 40
m 0 576 897 0
m 1 576 1114 0
c
w 40
m 0 576 909 0
m 1 576 1101 0
c
w 40
m 0 576 922 0
m 1 576 1088 0
c
w 40
m 0 576 933 0
m 1 576 1078 0
c
w 40
m 0 576 945 0
m 1 576 1065 0
c
w 40
m 0 576 958 0
m 1 576 1053 0
c
w 40
m 0 576 968 0
m 1 576 1042 0
c
w 40
u 0
u 1
c
w 40
c"""

    MNT.send(operations)
