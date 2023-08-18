from .config import get_config
from .imgreco import match_res
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


def run_startup():
    if not game_started():
        start_activity()
    while not on_status("main_menu"):
        if on_status("main_menu_btn_exist"):
            press_res("navigation.btn_main_menu")
        elif on_status("back_btn_exist"):
            press_res("navigation.btn_back")
        elif on_status("announcement"):
            press_res("startup.announcement.btn_close")
        elif on_status("splash"):
            press_res("startup.splash.enter")
        else:
            press_res("startup.main_menu.pos_wake")

