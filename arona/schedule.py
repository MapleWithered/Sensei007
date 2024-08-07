# TODO
import time

import numpy as np

from .adb import ADB
from .imgreco import match_res
from .ocr import OCR
from .presser import wait_res, press_res, wait_n_press_res, press_res_if_match
from .resource import res_value


def run_schedule():
    def goto_schedule():
        if match_res("schedule.anchor"):
            return
        while not match_res("schedule.anchor"):
            time.sleep(0.8)
            if match_res("startup.main_menu.anchor"):
                press_res("main_menu.btn_schedule")
                wait_res("schedule.anchor")
                return
            if press_res_if_match("navigation.btn_back"):
                continue
            if press_res_if_match("navigation.btn_main_menu"):
                continue
            press_res("navigation.btn_back")

    def handle_schedule():
        wait_n_press_res("schedule.btn_all_schedule")
        wait_res("schedule.title_all_schedule")
        time.sleep(1)

        color_avail = res_value("schedule.color_anchor.rgb.avail").split("-")
        color_done = res_value("schedule.color_anchor.rgb.done").split("-")
        color_locked = res_value("schedule.color_anchor.rgb.locked").split("-")
        color_empty = res_value("schedule.color_anchor.rgb.empty").split("-")

        screen_mat = ADB.screencap_mat(force=True)

        def color_in_range(screen_mat: np.ndarray, x: int, y: int, color: list[str], tolerance: int):
            return abs(screen_mat[y, x, 2] - int(color[0])) < tolerance and \
                   abs(screen_mat[y, x, 1] - int(color[1])) < tolerance and \
                   abs(screen_mat[y, x, 0] - int(color[2])) < tolerance

        status_list = []
        for tile in range(9):
            xy_pos: str = res_value(f"schedule.color_anchor.pos.{tile}")
            x, y = [int(_i) for _i in xy_pos.split("-")]
            if color_in_range(screen_mat, x, y, color_avail, 10):
                status_list.append("avail")
            elif color_in_range(screen_mat, x, y, color_done, 10):
                status_list.append("done")
            elif color_in_range(screen_mat, x, y, color_locked, 10):
                status_list.append("locked")
            elif color_in_range(screen_mat, x, y, color_empty, 10):
                status_list.append("empty")

        if "done" in status_list:
            press_res("schedule.btn_all_schedule")
            return {"succ": False, "status": "done"}

        if "avail" in status_list:
            # find avail from right to left
            for tile in range(8, -1, -1):
                if status_list[tile] == "avail":
                    press_res(f"schedule.color_anchor.pos.{tile}")
                    wait_res("schedule.title_schedule_info")
                    wait_n_press_res("schedule.btn_start_schedule", post_wait=1)
                    while not match_res("schedule.title_report"):
                        press_res("schedule.wait_report_empty_space")
                        time.sleep(1)
                    wait_n_press_res("schedule.btn_confirm_report")
                    wait_res("schedule.title_all_schedule")
                    press_res("schedule.btn_all_schedule")
                    return {"succ": True, "status": "success"}
        else:
            return {"succ": False, "status": "empty"}

    goto_schedule()

    ticket = int(OCR.ocr_res("schedule.ticket_ocr", mode='en', det='single_line')['text'][0])
    # TODO: total_ticket recognition

    if ticket != 0:
        wait_n_press_res("schedule.1st_level")

        for i in range(6):  # 6 buildings, edit this number for update
            succeeded = handle_schedule()['succ']
            if succeeded:
                ticket -= 1
            if ticket <= 0:
                break
            press_res("schedule.btn_next_building", 1.5)

    while not match_res("startup.main_menu.anchor"):
        res = False
        res = res or press_res_if_match("navigation.btn_main_menu")
        res = res or press_res_if_match("navigation.btn_back")
        if not res:
            press_res("navigation.btn_back")
    return
