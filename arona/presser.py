import time

from . import resource as res
from .adb import ADB
from .imgreco import match_res


def press_res(res_path: str, wait=1):
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


def wait_res(res_path: str, timeout=20):
    count = 0
    while not match_res(res_path):
        time.sleep(0.5)
        count += 1
        if count / 2 > timeout:
            return False
    return True


def press_res_if_match(res_path: str, wait=0.7):
    if match_res(res_path):
        press_res(res_path, wait)
        return True
    return False


def zoom_out(wait=0.7):
    ADB.input_zoom([1720, 540, 1120, 540], [200, 540, 800, 540])
    time.sleep(wait)
