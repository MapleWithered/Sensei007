import time

from .config import get_config
from .imgreco import match_res, compare_mat
from .presser import *


def game_started():
    res_window: str = ADB.get_device_object().shell("dumpsys window windows | grep -E 'BlueArchive'").strip()
    if res_window.find("BlueArchive") == -1:
        return False
    if res_window.find("mSurface") != -1:
        return True
    return False


def start_activity():
    command: str = get_config("arona.yaml/startup/command")
    package: str = get_config("arona.yaml/startup/package")
    activity: str = get_config("arona.yaml/startup/activity")
    ADB.get_device_object().shell(command.format(package=package, activity=activity))


def stop_activity():
    command = "am force-stop {package}"
    package: str = get_config("arona.yaml/startup/package")
    ADB.get_device_object().shell(command.format(package=package))


def on_status(status: str) -> bool:
    match status:
        case "splash":
            return match_res("startup.splash.anchor")
        case "announcement":
            return match_res("startup.announcement.anchor")
        case "main_menu":
            return match_res("startup.main_menu.anchor")
        case "main_menu_btn_exist":
            return match_res("navigation.btn_main_menu")
        case "back_btn_exist":
            return match_res("navigation.btn_back")
        case "upgrade_notification":
            return match_res("startup.upgrade.notification.anchor")
        case "battle_in_progress":
            return match_res("startup.battle_in_progress.notification.anchor")


def run_startup():
    screen_mat_prev = ADB.screencap_mat(force=True)
    stuck_counter = 0
    time_start = time.time()
    while time.time() - time_start < 2:
        screen_mat = ADB.screencap_mat(force=True)
        if not game_started():
            start_activity()
            time.sleep(3)
            time_start = time.time()
            screen_mat_prev = screen_mat
        if not on_status("main_menu"):
            if on_status("main_menu_btn_exist"):
                press_res("navigation.btn_main_menu")
            elif on_status("back_btn_exist"):
                press_res("navigation.btn_back")
            elif on_status("announcement"):
                press_res("startup.announcement.btn_close")
            elif on_status("splash"):
                press_res("startup.splash.enter")
            elif on_status("upgrade_notification"):
                press_res("startup.upgrade.notification.btn_confirm")
            elif on_status("battle_in_progress"):
                press_res("startup.battle_in_progress.notification.btn_abandon")
            else:
                if compare_mat(screen_mat, screen_mat_prev) > 0.999:
                    stuck_counter += 1
                else:
                    stuck_counter = 0
                    press_res("startup.main_menu.pos_wake")
                if stuck_counter > 5:
                    stop_activity()
                    time.sleep(3)
                    start_activity()
                    time.sleep(3)
                    stuck_counter = 0
            time_start = time.time()
            screen_mat_prev = screen_mat
        time.sleep(1.5)

