from . import presser
from .config import get_config
from .imgreco import find_res, remove_res_color, match_res_color, find_res_all, ocr_res
from .presser import *
from .resource import res_value, parse_rect


def handle_finish():
    wait_res("alchemy.anchor")
    find_result = find_res_all(f"alchemy.btn_take")
    btn_pos = [x['position'] for x in find_result]
    btn_pos.sort(key=lambda x: x[1])
    for btn in btn_pos:
        ADB.input_press_rect(*btn)
        wait_n_press_res("award.anchor", fore_wait=1, post_wait=1)
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
    print(title, "-", description)
    return len(priority_list) + 1


def handle_stage_two():
    # Wait for stage 2 to be displayed
    counter = 0
    while counter < 5:
        if not match_res("alchemy.stage2.anchor"):
            counter = 0
        else:
            counter += 1
            time.sleep(1)

    time.sleep(4)

    press_res("alchemy.stage2.badge_mid.1", wait=3)

    # Find furniture, find flower, find good things
    priority_list = []
    for i in range(5):
        press_res(f"alchemy.stage2.badge_left.{i + 1}", wait=1)
        title = ocr_res("alchemy.stage2.ocr_title", mode='cn', std=True)[0]['text']
        description = ocr_res("alchemy.stage2.ocr_description", mode='cn', std=True)[0]['text']
        priority_list.append((i, match_priority(title, description)))
    priority_list.sort(key=lambda x: x[1])
    press_res(f"alchemy.stage2.badge_left.{priority_list[0][0] + 1}", wait=1)

    wait_n_press_res("alchemy.stage2.btn_confirm", post_wait=4)
    wait_n_press_res("alchemy.stage2.btn_start", fore_wait=3, post_wait=8)

    wait_res("alchemy.anchor")


def handle_new():
    wait_res("alchemy.anchor")
    find_result = find_res_all(f"alchemy.btn_new")
    btn_pos = [x['position'] for x in find_result]
    btn_pos.sort(key=lambda x: x[1])
    for btn in btn_pos:
        ADB.input_press_rect(*btn)
        wait_res("alchemy.stage1.btn_start_unavailable")
        time.sleep(0.5)

        # TODO: Stage 1, select hearthstone

        f_succeed = handle_stage_one()

        if not f_succeed:
            return

        # TODO: Stage 2

        handle_stage_two()

        wait_res("alchemy.anchor")


def handle_stage_one():
    if not match_res("alchemy.stage1.stone_avail_big"):
        # No hearthstone available
        return False
    # Select big hearthstone and goto stage 2
    press_res("alchemy.stage1.stone_avail_big")
    wait_res("alchemy.stage1.btn_start_available")
    press_res("alchemy.stage1.btn_start_available")
    return True


def run_alchemy():
    # print(ADB.screencap_mat(force=True)[1009, 1092][::-1])
    wait_res("startup.main_menu.anchor")
    wait_n_press_res("main_menu.btn_alchemy")
    time.sleep(7)
    wait_res("navigation.btn_main_menu")

    # If already at stage 2, handle stage 2 first
    if match_res("alchemy.stage2.anchor"):
        handle_stage_two()
    if match_res("alchemy.stage2.btn_start"):
        wait_n_press_res("alchemy.stage2.btn_start", fore_wait=3, post_wait=8)
        wait_res("alchemy.anchor")

    handle_finish()

    handle_new()

    # Back to main menu
    while not match_res("startup.main_menu.anchor"):
        press_res_if_match("navigation.btn_main_menu")
        time.sleep(3)
