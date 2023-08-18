from .config import get_config
from .imgreco import match_res, compare_mat, find_res
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
    while True:
        x1, y1, x2, y2 = res_value("momotalk.dialog_box").split("-")
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        prev_mat_diag = ADB.screencap_mat()[y1:y2, x1:x2]
        time.sleep(5)
        mat_diag = ADB.screencap_mat()[y1:y2, x1:x2]
        while compare_mat(mat_diag, prev_mat_diag) < 0.95:
            prev_mat_diag = mat_diag
            mat_diag = ADB.screencap_mat()[y1:y2, x1:x2]
            time.sleep(5)
        v, _, _, ax, ay, val = find_res("momotalk.reply_title", norm=False)
        print(val)
        if v:
            ADB.input_press_pos(ax, ay + res_value("momotalk.reply_dy"))
            continue
        v, _, _, ax, ay, val = find_res("momotalk.story_title", norm=False)
        print(val)
        if v:
            ADB.input_press_pos(ax, ay + res_value("momotalk.story_dy"))
            wait_n_press_res("momotalk.story_enter")
            wait_n_press_res("story.menu_anchor", fore_wait=5)
            wait_n_press_res("story.btn_skip")
            wait_n_press_res("story.confirm_skip")
            wait_n_press_res("award.anchor", fore_wait=5)
            continue
        # elif match_res("momotalk.btn_event_story"):
        press_res("momotalk.second_msg")
        press_res("momotalk.first_msg.empty")
        break


def run_momotalk():
    assert match_res("momotalk.anchor")
    if not match_res("momotalk.btn_message_activated"):
        press_res("momotalk.btn_message_activated")
    if not match_res("momotalk.btn_unread"):
        press_res("momotalk.btn_unread")
        press_res("momotalk.step_unread.1")
        press_res("momotalk.step_unread.2")
    if not match_res("momotalk.btn_sorted"):
        press_res("momotalk.btn_sorted")

    while True:
        press_res("momotalk.btn_sorted")
        press_res("momotalk.btn_sorted")
        if match_res("momotalk.first_msg.empty"):
            break

        press_res("momotalk.first_msg.empty")
        handle_dialogue()

    press_res("momotalk.btn_close")