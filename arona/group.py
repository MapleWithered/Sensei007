from .imgreco import match_res_color
from .presser import wait_res, wait_n_press_res


def run_group():
    # print(ADB.screencap_mat(force=True)[1011, 920][::-1])
    wait_res("startup.main_menu.anchor")
    if not match_res_color("main_menu.badge_group"):
        return
    wait_n_press_res("main_menu.btn_group")

    wait_n_press_res("group.sign_in_notification.btn_comfirm")

    wait_n_press_res("navigation.btn_main_menu", post_wait=4)
    wait_res("startup.main_menu.anchor")
