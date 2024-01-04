from . import presser
from .config import get_config
from .imgreco import find_res, remove_res_color, match_res_color, find_res_all, ocr_res
from .presser import *
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

    # Find furniture, find flower, find good things
    priority_list = []
    for i in range(5):
        press_res(f"alchemy.stage2.badge_left.{i + 1}", wait=0.25)
        title = ocr_res("alchemy.stage2.ocr_title", mode='cn', std=True, force=True)[0]['text']
        description = ocr_res("alchemy.stage2.ocr_description", mode='cn', std=True)[0]['text']
        priority_list.append((i, match_priority(title, description)))
    priority_list.sort(key=lambda x: x[1])
    press_res(f"alchemy.stage2.badge_left.{priority_list[0][0] + 1}", wait=0.3)

    wait_n_press_res("alchemy.stage2.btn_confirm", post_wait=2)
    wait_n_press_res("alchemy.stage2.btn_start", fore_wait=0.5, post_wait=4)

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
    time.sleep(2)
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
