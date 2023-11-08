from .config import get_config
from .imgreco import *
from .presser import *
from .resource import res_value


def on_status(status: str) -> bool:
    match status:
        case "momo_main":
            return match_res("startup.splash.anchor")
        case "announcement":
            return match_res("startup.announcement.anchor")
        case "main_menu":
            return match_res("startup.main_menu.anchor")
        case "main_menu_btn_exist":
            return match_res("navigation.btn_main_menu")
        case "back_btn_exist":
            return match_res("navigation.btn_back")


def handle_dialogue():
    x1, y1, x2, y2 = res_value("momotalk.dialog_box").split("-")
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    prev_mat_diag = None
    time_start = time.time()
    while time.time() - time_start < 4:
        mat_diag = ADB.screencap_mat(force=True)[y1:y2, x1:x2]

        v, _, _, ax, ay, val = find_res("momotalk.reply_title", norm=True)
        if v:
            ADB.input_press_pos(ax, ay + res_value("momotalk.reply_dy"))
            time.sleep(0.7)
            time_start = time.time()
            continue

        v, _, _, ax, ay, val = find_res("momotalk.story_title", norm=True, threshold=0.99)
        if v:
            ADB.input_press_pos(ax, ay + res_value("momotalk.story_dy"))
            while True:
                press_res_if_match("momotalk.story_enter")
                press_res_if_match("story.menu_anchor")
                press_res_if_match("story.btn_skip")
                if press_res_if_match("story.confirm_skip"):
                    break
                time.sleep(0.3)
            wait_n_press_res("award.anchor", fore_wait=0, post_wait=1)
            time_start = time.time()
            continue

        # if prev_mat_diag is not None:
        #     print(compare_mat(mat_diag, prev_mat_diag))
        if prev_mat_diag is not None and compare_mat(mat_diag, prev_mat_diag) < 0.999:
            time_start = time.time()

        prev_mat_diag = mat_diag
        continue

    press_res("momotalk.second_msg")
    press_res("momotalk.first_msg.empty")


def run_momotalk():
    print(ADB.screencap_mat(force=True)[190, 284][::-1])
    wait_res("startup.main_menu.anchor")
    if not match_res_color("main_menu.badge_momotalk"):
        return
    while match_res_color("main_menu.badge_momotalk") or match_res("startup.main_menu.anchor"):
        press_res("main_menu.badge_momotalk.pos", 2)

    wait_res("momotalk.anchor")
    if not match_res("momotalk.btn_message_activated"):
        press_res("momotalk.btn_message_activated")
    if not match_res("momotalk.btn_unread"):
        press_res("momotalk.btn_unread")
        press_res("momotalk.step_unread.1")
        press_res("momotalk.step_unread.2", 1)
    if not match_res("momotalk.btn_sorted"):
        press_res("momotalk.btn_sorted")

    while True:
        press_res("momotalk.btn_sorted")
        press_res("momotalk.btn_sorted", wait=2.5)
        ADB.screencap_mat(force=True)
        if not match_res_color("momotalk.badge_unread"):
            break

        press_res("momotalk.first_msg.empty")
        handle_dialogue()

    press_res("momotalk.btn_close")
    wait_res("startup.main_menu.anchor")
