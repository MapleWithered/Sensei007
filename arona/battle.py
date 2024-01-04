import time

from .imgreco import *
from .presser import wait_res, press_res, wait_n_press_res, press_res_if_match
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
    # print(stage_list)


def run_wanted():
    # TODO: Change all wait main menu to goto main menu
    wait_res("startup.main_menu.anchor")

    press_res("main_menu.btn_terminal")
    wait_res("terminal.anchor")

    wait_n_press_res("terminal.btn_wanted", post_wait=2)
    wait_res("wanted.btn_1")

    for i in range(3):
        if match_res(f"wanted.anchor_empty.{i + 1}", 0.99):
            continue
        wait_n_press_res(f"wanted.btn_{i + 1}", post_wait=2)
        wait_res("wanted.stage_anchor")
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
        time.sleep(0.8)
        wait_res("battle.anchor_battle_info")
        press_res("battle.btn_count_plus", wait=1)
        if match_res("battle.count_zero"):
            press_res("terminal.btn_back", wait=1)
            press_res("terminal.btn_back", wait=2)
            continue
        for _ in range(10):
            press_res("battle.btn_count_plus", wait=0.2)
        wait_n_press_res("battle.btn_start_skip", fore_wait=0.5, post_wait=1)
        wait_n_press_res("battle.btn_confirm_skip", fore_wait=0.5, post_wait=8)
        wait_res("battle.anchor_finish_skip_battle")
        wait_n_press_res("battle.btn_confirm_finish", post_wait=5)
        while not match_res(f"wanted.btn_{i + 1}"):
            press_res("terminal.btn_back", wait=3)
    time.sleep(1)
    press_res("navigation.btn_main_menu", wait=1.5)
    wait_res("startup.main_menu.anchor")


def run_competition():
    def goto_competition():
        if match_res("competition.anchor"):
            return
        while not match_res("competition.anchor"):
            time.sleep(2)
            if match_res("startup.main_menu.anchor"):
                press_res("main_menu.btn_terminal")
                wait_res("terminal.anchor")
            if match_res("terminal.btn_competition"):
                press_res("terminal.btn_competition")
                wait_res("competition.anchor")
                return
            if press_res_if_match("navigation.btn_back"):
                continue
            if press_res_if_match("navigation.btn_main_menu"):
                continue
            press_res("navigation.btn_back")

    def handle_battle():
        wait_n_press_res("competition.btn_enter_team")
        wait_res("competition.label_skip")
        if not match_res("competition.tickbox_skip"):
            press_res("competition.tickbox_skip")
        while (match_res("competition.title_cooling") or
                match_res("competition.title_cooling_emptytimer") or
               (not match_res("competition.btn_confirm_result_win") and not match_res("competition.btn_confirm_result_lose"))):
            if match_res("competition.label_skip") or match_res("competition.title_cooling"):
                press_res("competition.btn_start_battle")
            time.sleep(1)

        succ = True
        while not match_res("competition.anchor"):
            if press_res_if_match("competition.btn_confirm_result_win"):
                succ = True
            elif press_res_if_match("competition.btn_confirm_result_lose"):
                succ = False
            else:
                press_res_if_match("competition.btn_confirm_best_record")

        return succ

    goto_competition()

    if press_res_if_match("competition.btn_award_time_avail"):
        wait_n_press_res("award.anchor", fore_wait=0, post_wait=1)

    if press_res_if_match("competition.btn_award_daily_avail"):
        wait_n_press_res("award.anchor", fore_wait=0, post_wait=1)

    my_level = int(ocr_res("competition.my_level_ocr", mode='digit', std=False)['text'])

    stair_allow = 1

    counter = 0

    while stair_allow <= 3:
        res = ocr_res("competition.ticket_ocr", mode='en', std=False)
        if res['text'][0] not in ['1', '2', '3', '4', '5']:
            break

        levels = [int(ocr_res(f"competition.level_ocr.{i}", mode='digit', std=False)['text']) for i in range(1, 4)]
        # print(levels)

        for i in range(1, stair_allow + 1):
            if levels[i - 1] < my_level:
                press_res(f"competition.level_ocr.{i}")
                handle_battle()
                break
        else:
            press_res("competition.btn_update", wait=1)
            while ADB.is_loading():
                time.sleep(1)
            counter += 1

        if counter >= 20:
            counter = 0
            stair_allow += 1

    if press_res_if_match("competition.btn_award_time_avail"):
        wait_n_press_res("award.anchor", fore_wait=0, post_wait=1)

    if press_res_if_match("competition.btn_award_daily_avail"):
        wait_n_press_res("award.anchor", fore_wait=0, post_wait=1)


    while not match_res("startup.main_menu.anchor"):
        res = False
        res = res or press_res_if_match("navigation.btn_main_menu")
        res = res or press_res_if_match("navigation.btn_back")
        if not res:
            press_res("navigation.btn_back")
    return


def run_story():
    pass
