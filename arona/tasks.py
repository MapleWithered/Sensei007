from . import presser
from .config import get_config
from .imgreco import find_res, remove_res_color, match_res_color
from .presser import *
from .resource import res_value, parse_rect

def run_tasks():
    wait_res("startup.main_menu.anchor")
    if not match_res_color("main_menu.badge_task"):
        return
    wait_n_press_res("main_menu.btn_tasks")

    time.sleep(2.8)
    wait_res("navigation.btn_main_menu")

    counter = 0

    while counter < 6:
        res = False
        res = res or press_res_if_match("tasks.btn_take_all")
        res = res or press_res_if_match("award.anchor")
        res = res or press_res_if_match("tasks.btn_notify_limit_break_confirm")
        if not res:
            counter += 1
        else:
            counter = 0

    while not match_res("startup.main_menu.anchor"):
        res = False
        res = res or press_res_if_match("navigation.btn_main_menu")
        res = res or press_res_if_match("navigation.btn_back")
        if not res:
            press_res("navigation.btn_back")

