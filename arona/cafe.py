from . import presser
from .config import get_config
from .imgreco import find_res, remove_res_color, match_res_color
from .presser import *
from .resource import res_value, parse_rect


def handle_characters():
    for _ in range(8):
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
        for c in contours:
            # Calculate the moments of the contour
            moments = cv2.moments(c)

            xx, yy, ww, hh = cv2.boundingRect(c)

            # Calculate the centroid of the contour
            cx = int(moments['m10'] / moments['m00'])
            cy = yy + hh - 100

            illegal = 0
            for i in range(len(res_value(f"cafe.mask_neglect"))):
                x1, y1, x2, y2 = parse_rect(res_value(f"cafe.mask_neglect.{i}"))
                if x1 < cx < x2 and y1 < cy < y2:
                    illegal = 1

            if illegal:
                continue

            ADB.input_press_pos(cx, cy)
        # cv2.waitKey(0)

def run_cafe():
    wait_res("startup.main_menu.anchor")
    if not match_res_color("main_menu.badge_cafe"):
        return
    wait_n_press_res("main_menu.btn_cafe")

    time.sleep(2)
    while not match_res("navigation.btn_main_menu"):
        press_res_if_match("cafe.btn_visit_confirm")

    time.sleep(2)
    if match_res("cafe.btn_invite_avail"):
        press_res("cafe.btn_invite_avail")
        # TODO: handle invite people choose logic
        print("Please invite your student")
        wait_res("cafe.btn_preset")

    v, _, _, ax, ay, val = find_res("cafe.bubble_can_take", norm=False, threshold=0.985)
    if v:
        press_res("cafe.btn_profit")
        wait_n_press_res("cafe.btn_profit_take")
        wait_n_press_res("award.anchor", fore_wait=5, post_wait=2)
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
    time.sleep(3)
    swipe_res("cafe.swipe.1")
    handle_characters()

    presser.zoom_out()
    time.sleep(3)
    swipe_res("cafe.swipe.2")
    handle_characters()

    press_res("cafe.btn_expand_panel")
    wait_n_press_res("cafe.btn_preset_moved")
    wait_n_press_res(f"cafe.preset.btn_apply.{num_preset}")
    wait_n_press_res("cafe.preset.btn_save.save_confirm")
    wait_res(f"cafe.preset.btn_save.{num_preset}")
    press_res("cafe.preset.btn_close")

    press_res("navigation.btn_main_menu")
    wait_res("startup.main_menu.anchor")

