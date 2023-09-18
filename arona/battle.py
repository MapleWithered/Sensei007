import time

from .imgreco import *
from .presser import wait_res, press_res, wait_n_press_res
from .resource import res_value


def get_level():
    wait_res("battle.level_anchor")
    return ocr_res("battle.level_ocr", mode='digit', std=False)['text']


def is_hard():
    wait_res("battle.level_anchor")
    return match_res_color("battle.hard_chosen")


def get_stage_list():
    level = get_level()
    hard = "H" if is_hard() else ''
    find_stages = find_res_all(f"battle.btn_enter_stage{hard}")
    list_pos = [[x['position'][0], x['position'][1]] for x in find_stages]
    list_pos.sort(key=lambda x: x[1])
    dx = res.res_value(f"battle.btn_to_stage{hard}_deviation.dx")
    dy = res.res_value(f"battle.btn_to_stage{hard}_deviation.dy")
    width = res.res_value("battle.stage_name.width")
    height = res.res_value("battle.stage_name.height")
    list_pos = [[x[0] + dx, x[1] + dy, x[0] + dx + width, x[1] + dy + height] for x in list_pos]
    stage_list = ocr_list(list_pos, mode='cn', force=False)
    # print(stage_list)
    for stage in stage_list:
        stage['text'] = stage['text'].replace(' ', '').replace('—', '-').replace('一', '-').replace('O', '0')
    stage_list = [[hard + stage_list[i]['text'], list_pos[i]] for i in range(len(stage_list)) if
                  stage_list[i]['text'].split('-')[0] == str(level)]
    print(stage_list)


def run_wanted():
    # TODO: Change all wait main menu to goto main menu
    wait_res("startup.main_menu.anchor")

    press_res("main_menu.btn_terminal")
    wait_res("terminal.anchor")

    wait_n_press_res("terminal.btn_wanted", post_wait=2)

    for i in range(3):
        wait_n_press_res(f"wanted.btn_{i + 1}", post_wait=3)
        res_list = find_res_all("wanted.3_star")
        res_list.sort(key=lambda x: x['position'][1])
        if len(res_list) == 0:
            press_res("terminal.btn_back", wait=3)
            continue
        dx = res_value("wanted.delta_3_star_to_btn_start.dx")
        dy = res_value("wanted.delta_3_star_to_btn_start.dy")
        width = res_value("wanted.btn_start.width")
        height = res_value("wanted.btn_start.height")
        star_pos = res_list[-1]['position']
        btn_pos = [star_pos[0] + dx, star_pos[1] + dy, star_pos[0] + dx + width, star_pos[1] + dy + height]
        ADB.input_press_rect(*btn_pos)
        time.sleep(3)
        wait_res("battle.anchor_battle_info")
        press_res("battle.btn_count_plus", wait=2)
        if match_res("battle.count_zero"):
            press_res("terminal.btn_back", wait=1.5)
            press_res("terminal.btn_back", wait=3)
            continue
        for _ in range(10):
            press_res("battle.btn_count_plus", wait=0.2)
        wait_n_press_res("battle.btn_start_skip", fore_wait=0.5, post_wait=1)
        wait_n_press_res("battle.btn_confirm_skip", fore_wait=0.5, post_wait=8)
        wait_res("battle.anchor_finish_skip_battle")
        wait_n_press_res("battle.btn_confirm_finish", post_wait=5)
        while not match_res(f"wanted.btn_{i + 1}"):
            press_res("terminal.btn_back", wait=3)
    time.sleep(2)
    press_res("navigation.btn_main_menu", wait=5)
    wait_res("startup.main_menu.anchor")


def run_competition():
    pass


def run_story():
    pass
