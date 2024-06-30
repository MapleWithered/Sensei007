import time

import cv2

from .adb import ADB
from .config import get_config
from .imgreco import find_res_all, match_res
from .ocr import OCR
from .presser import wait_res, press_res, wait_n_press_res
from .resource import res_value, parse_rect


def handle_finish(boost=False):
    wait_res("alchemy.anchor")
    if boost:
        find_result = find_res_all(f"alchemy.btn_fast_finish")
        btn_pos = [x['position'] for x in find_result]
        btn_pos.sort(key=lambda x: x[1])
        for btn in btn_pos:
            ADB.input_press_rect(*btn)
            wait_res("alchemy.fast_finish.anchor")
            press_res("alchemy.fast_finish.btn_confirm")
            press_res("alchemy.fast_finish.btn_cancel")
            wait_res("alchemy.anchor")
    find_result = find_res_all(f"alchemy.btn_take")
    btn_pos = [x['position'] for x in find_result]
    btn_pos.sort(key=lambda x: x[1])
    for btn in btn_pos:
        ADB.input_press_rect(*btn)
        wait_n_press_res("award.anchor", fore_wait=0, post_wait=0.5)
        wait_res("alchemy.anchor")


def match_priority(title, description):
    # priority: smaller is better
    priority_list_raw: list[str] = get_config("user_config.yaml/task.alchemy.priority")
    priority_list = []
    for item in priority_list_raw:
        item.replace(' ', '')
        category, name = item.split(':')
        priority_list.append((category, name))
    for i in range(len(priority_list)):
        category, name = priority_list[i]
        if category == 'title':
            if name in title:
                return i
        elif category == 'description':
            if name in description:
                return i
    # print(title, "-", description)
    return len(priority_list) + 1


def check_color_left():
    img_screen = ADB.screencap_mat()
    rect_list = [parse_rect(res_value(f"alchemy.stage2.badge_left.{i + 1}")) for i in range(5)]
    mid_point_list = []
    for rect in rect_list:
        mid_point_list.append(((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2))
        mid_point_list.sort(key=lambda x: -x[1])
    for i in range(5):
        rect_list[i] = [mid_point_list[i][0] - 10, mid_point_list[i][1] - 10, mid_point_list[i][0] + 10,
                        mid_point_list[i][1] + 10]
    # for i in range(5):
    # cv2.imshow(f"i={i}", img_screen[int(rect_list[i][1]):int(rect_list[i][3]), int(rect_list[i][0]):int(rect_list[i][2])])
    # cv2.waitKey(0)
    # rect -> HSV -> average of HSV -> hue as color
    color_list = []
    index_list = []
    for i, rect in enumerate(rect_list):
        img = img_screen[int(rect[1]):int(rect[3]), int(rect[0]):int(rect[2])]
        img = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)
        h, l, s = cv2.split(img)
        color_list.append((h.mean(), s.mean(), l.mean()))
        if s.mean() < 145:
            index_list.append(i)
    print(color_list)
    return index_list


def handle_stage_two():
    # Wait for stage 2 to be displayed
    counter = 0
    while counter < 2:
        if not match_res("alchemy.stage2.anchor"):
            counter = 0
        else:
            counter += 1
            time.sleep(1)

    press_res("alchemy.stage2.badge_mid.1", wait=1.3)

    # find gold
    gold_index = check_color_left()

    # Find furniture, find flower, find good things
    priority_list = []
    for i in range(5):
        press_res(f"alchemy.stage2.badge_left.{i + 1}", wait=0.25)
        title = OCR.ocr_res("alchemy.stage2.ocr_title", mode='cn', det='std', force=True)[0]['text']
        description = OCR.ocr_res("alchemy.stage2.ocr_description", mode='cn', det='std')[0]['text']
        priority_list.append((i, match_priority(title, description)))
        if i in gold_index:
            priority_list[-1] = (i, priority_list[-1][1] - 100)
    priority_list.sort(key=lambda x: x[1])
    press_res(f"alchemy.stage2.badge_left.{priority_list[0][0] + 1}", wait=0.3)

    wait_n_press_res("alchemy.stage2.btn_confirm", post_wait=2)
    wait_n_press_res("alchemy.stage2.btn_start", fore_wait=0.5, post_wait=2)
    wait_n_press_res("alchemy.stage2.btn_notification_confirm", fore_wait=0.5, post_wait=4)

    wait_res("alchemy.anchor")


def handle_new():
    wait_res("alchemy.anchor")
    find_result = find_res_all(f"alchemy.btn_new")
    btn_pos = [x['position'] for x in find_result]
    btn_pos.sort(key=lambda x: x[1])
    if len(btn_pos) == 0:
        return False
    for btn in btn_pos:
        ADB.input_press_rect(*btn)
        wait_res("alchemy.stage1.btn_start_unavailable")
        time.sleep(0.5)

        # TODO: Stage 1, select hearthstone

        f_succeed = handle_stage_one()

        if not f_succeed:
            press_res("navigation.btn_back", wait=0.5)
            wait_res("alchemy.anchor")
            return False

        # TODO: Stage 2

        handle_stage_two()

        wait_res("alchemy.anchor")

    return True


def handle_stage_one():
    if match_res("alchemy.stage1.stone_avail_big"):
        # Select big hearthstone and goto stage 2
        press_res("alchemy.stage1.stone_avail_big", wait=0.35)
        wait_n_press_res("alchemy.stage1.btn_start_available")
        return True
    elif match_res("alchemy.stage1.stone_avail_small", threshold=0.99):
        for i in range(10):
            press_res("alchemy.stage1.stone_avail_small", wait=0.12)
        time.sleep(0.35)
        if not match_res("alchemy.stage1.btn_start_available"):
            return False
        press_res("alchemy.stage1.btn_start_available")
        return True
    else:
        # No hearthstone available
        return False


def run_alchemy(boost=False):
    # print(ADB.screencap_mat(force=True)[1009, 1092][::-1])
    wait_res("startup.main_menu.anchor")
    wait_n_press_res("main_menu.btn_alchemy")
    time.sleep(4)
    wait_res("navigation.btn_main_menu")

    if not match_res("alchemy.anchor"):
        # If already at stage 2, handle stage 2 first
        if match_res("alchemy.stage2.anchor"):
            handle_stage_two()
        if match_res("alchemy.stage2.btn_start"):
            wait_n_press_res("alchemy.stage2.btn_start", fore_wait=3, post_wait=8)
            wait_res("alchemy.anchor")

    remain = True

    while remain:
        handle_finish(boost=boost)
        remain = handle_new()

    handle_finish(boost=boost)

    # Back to main menu
    wait_n_press_res("navigation.btn_main_menu")
    wait_res("startup.main_menu.anchor")
