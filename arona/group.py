from . import presser
from .config import get_config
from .imgreco import find_res, remove_res_color, match_res_color
from .presser import *
from .resource import res_value, parse_rect

def run_group():
    # print(ADB.screencap_mat(force=True)[1011, 920][::-1])
    wait_res("startup.main_menu.anchor")
    if not match_res_color("main_menu.badge_group"):
        return
    wait_n_press_res("main_menu.btn_group")

    wait_n_press_res("group.sign_in_notification.btn_comfirm")

    wait_n_press_res("navigation.btn_main_menu", post_wait=4)
    wait_res("startup.main_menu.anchor")
