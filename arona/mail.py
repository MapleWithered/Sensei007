from . import presser
from .config import get_config
from .imgreco import find_res, remove_res_color, match_res_color
from .presser import *
from .resource import res_value, parse_rect

def run_mail():
    # print(ADB.screencap_mat(force=True)[25, 1767][::-1])
    wait_res("startup.main_menu.anchor")
    if not match_res_color("main_menu.badge_mail"):
        return
    wait_n_press_res("main_menu.btn_mail")

    time.sleep(2.8)
    wait_res("navigation.btn_main_menu")

    counter = 0
    while counter < 5:
        if match_res("mail.btn_take_all"):
            counter = 0
            press_res("mail.btn_take_all")
            wait_n_press_res("award.anchor", fore_wait=1, post_wait=3)
            press_res_if_match("award.btn_notification_close", wait=1)
        else:
            counter += 1
        time.sleep(0.5)

    wait_n_press_res("navigation.btn_main_menu")
    wait_res("startup.main_menu.anchor")
