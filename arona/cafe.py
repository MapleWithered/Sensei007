import numpy as np

from . import presser
from .config import get_config
from .imgreco import find_res, remove_res_color, match_res_color, find_res_all, ocr_list
from .presser import *
from .resource import res_value, parse_rect


def get_invite_list():
    wait_res("cafe.visit.anchor")
    find_students = find_res_all(f"cafe.visit.btn_invite", force=True)
    btn_pos = [x['position'] for x in find_students]
    btn_pos.sort(key=lambda x: x[1])
    dx = res.res_value(f"cafe.visit.btn_to_name_deviation.dx")
    dy = res.res_value(f"cafe.visit.btn_to_name_deviation.dy")
    width = res.res_value("cafe.visit.name.width")
    height = res.res_value("cafe.visit.name.height")
    list_pos = [[x[0] + dx, x[1] + dy, x[0] + dx + width, x[1] + dy + height] for x in btn_pos]
    student_list = ocr_list(list_pos, mode='cn', force=False)
    # print(student_list)
    student_list = [[student_list[i]['text'], list_pos[i], btn_pos[i]] for i in range(len(student_list))]
    return student_list


def find_student(stu: str):
    wait_res("cafe.visit.anchor")
    if match_res("cafe.visit.btn_school"):
        press_res("cafe.visit.btn_school")
        wait_res("cafe.visit.btn_confirm_sort_cat")
        press_res("cafe.visit.btn_sort_cat_level")
        press_res("cafe.visit.btn_confirm_sort_cat")
    press_res_if_match("cafe.visit.btn_sort_up")
    direction = 'down'
    stu_name_list = None
    prev_name_list = None
    empty_count = 0
    while empty_count < 5:
        stu_list = get_invite_list()
        stu_name_list = [stu_list[i][0] for i in range(len(stu_list))]
        # print(stu_name_list)
        for i in range(len(stu_list)):
            if stu_list[i][0] == stu:
                return stu_list[i][2]
        if stu_name_list == prev_name_list:
            direction = 'up' if direction == 'down' else 'down'
            empty_count += 1
        swipe_res(f"cafe.visit.swipe.{direction}")
        time.sleep(1.2)
        prev_name_list = stu_name_list
    return None


def handle_characters():
    counter = 0
    while counter < 16:
        counter += 1
        if match_res("cafe.anchor_doki"):
            counter = 0
            time.sleep(2)
            press_res("cafe.anchor_doki")
            time.sleep(2)
        mat = ADB.screencap_mat(force=True)
        for i in range(len(res_value(f"cafe.mask_neglect"))):
            x1, y1, x2, y2 = parse_rect(res_value(f"cafe.mask_neglect.{i}"))
            mat[y1:y2, x1:x2] = 0
        # cv2.imshow("0", mat)
        mat = remove_res_color(mat, "cafe.color_neglect")
        # cv2.imshow("1", mat)
        mat = cv2.erode(mat, np.ones((4, 4), np.uint8), iterations=2)
        # cv2.imshow("2", mat)
        mat = cv2.dilate(mat, np.ones((25, 25), np.uint8), iterations=3)
        # cv2.imshow("3", mat)
        gray = cv2.cvtColor(mat, cv2.COLOR_BGR2GRAY)
        contours, _ = cv2.findContours(gray.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mat = cv2.drawContours(mat, contours, -1, (0, 255, 0), 2)
        # cv2.imshow("4", mat)
        X = []
        Y = []
        for c in contours:
            # Calculate the moments of the contour
            moments = cv2.moments(c)

            xx, yy, ww, hh = cv2.boundingRect(c)

            # Calculate the centroid of the contour
            X.append(int(moments['m10'] / moments['m00']))
            Y.append(yy + hh - 100)

        # if counter > 10:
        #     X_ex = []
        #     X_ey = []
        #     dx_step = 25
        #     dy_step = 40
        #     for dy in range(0, 3 + 1):
        #         for dx in range(0, 3 + 1):
        #             for i in range(len(X)):
        #                 X_ex.append(X[i] + dx * dx_step)
        #                 X_ex.append(X[i] - dx * dx_step)
        #                 X_ey.append(Y[i] + dy * dy_step)
        #                 X_ey.append(Y[i] - dy * dy_step)
        #                 X_ex.append(X[i] + dx * dx_step)
        #                 X_ex.append(X[i] - dx * dx_step)
        #                 X_ey.append(Y[i] - dy * dy_step)
        #                 X_ey.append(Y[i] + dy * dy_step)
        #     X.extend(X_ex)
        #     Y.extend(X_ey)

        for i in range(len(X)):
            illegal = 0
            for j in range(len(res_value(f"cafe.mask_neglect"))):
                x1, y1, x2, y2 = parse_rect(res_value(f"cafe.mask_neglect.{j}"))
                if x1 < X[i] < x2 and y1 < Y[i] < y2:
                    illegal = 1
            if illegal:
                continue
            ADB.input_press_pos(X[i], Y[i])
            time.sleep(0.1)
        # cv2.waitKey(0)


def run_cafe(force=False):
    wait_res("startup.main_menu.anchor")
    if not force and not match_res_color("main_menu.badge_cafe"):
        return
    wait_n_press_res("main_menu.btn_cafe")

    time.sleep(2)
    while not match_res("navigation.btn_main_menu"):
        press_res_if_match("cafe.btn_visit_confirm")

    time.sleep(2)
    if match_res("cafe.btn_invite_avail"):
        press_res("cafe.btn_invite_avail")
        stu_name = get_config("user_config.yaml/task.cafe.invite")
        res = find_student(stu_name)
        # TODO: use name_list match instead of single student
        if res is None:
            press_res("cafe.visit.btn_close", 2)
        else:
            ADB.input_press_rect(*res)
            wait_n_press_res("cafe.visit.btn_confirm_invite")
            time.sleep(5)

    v1, _, _, _, _, _ = find_res("cafe.bubble_can_take", norm=True, threshold=0.985)
    v2, _, _, _, _, _ = find_res("cafe.bubble_full", norm=True, threshold=0.985)
    if v1 or v2:
        wait_n_press_res("cafe.btn_profit")
        wait_n_press_res("cafe.btn_profit_take")
        wait_n_press_res("award.anchor", fore_wait=0, post_wait=0.25)
        wait_n_press_res("cafe.btn_profit_close", post_wait=2)



    wait_n_press_res("cafe.btn_preset")
    num_preset = get_config("user_config.yaml/cafe.empty_preset_slot")
    time.sleep(2)
    if not match_res(f"cafe.preset.btn_apply.{num_preset}"):
        wait_n_press_res(f"cafe.preset.btn_save.{num_preset}")
        wait_n_press_res("cafe.preset.btn_save.save_confirm")
        wait_res(f"cafe.preset.btn_save.{num_preset}")
    press_res("cafe.preset.btn_close")
    wait_n_press_res("cafe.btn_hide_all")
    wait_n_press_res("cafe.preset.btn_save.save_confirm")

    wait_res("cafe.btn_preset")
    press_res("cafe.btn_hide_panel")

    presser.zoom_out()
    swipe_res("cafe.swipe.1")
    handle_characters()

    presser.zoom_out()
    swipe_res("cafe.swipe.2")
    handle_characters()

    if not match_res("cafe.btn_preset_moved") and not match_res("cafe.btn_hide_all"):
        press_res("cafe.btn_expand_panel", wait=2)
    wait_n_press_res("cafe.btn_preset_moved")
    wait_n_press_res(f"cafe.preset.btn_apply.{num_preset}")
    wait_n_press_res("cafe.preset.btn_save.save_confirm", post_wait=2)
    wait_res(f"cafe.preset.btn_save.{num_preset}")
    wait_n_press_res("cafe.preset.btn_close")

    wait_n_press_res("navigation.btn_main_menu")
    wait_res("startup.main_menu.anchor")

    # TODO: handle the counter down timer of invitation
