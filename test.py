
import cv2
import time

import numpy as np

from arona.adb import ADB
from arona.imgreco import find_res, remove_res_color
from arona.resource import parse_rect, res_value
#
# fps = 1  # 帧率
# pre_frame = None  # 总是取前一帧做为背景（不用考虑环境影响）
#
# play_music = False
#
# while True:
#     # start = time.time()
#     time.sleep(1)
#     cur_frame = ADB.screencap_mat()
#     # end = time.time()
#     # seconds = end - start
#     # if seconds < 1.0 / fps:
#         # time.sleep(1.0 / fps - seconds)
#
#     gray_img = cv2.cvtColor(cur_frame, cv2.COLOR_BGR2GRAY)
#     # gray_img = cv2.resize(gray_img, (500, 500))
#     gray_img = cv2.GaussianBlur(gray_img, (21, 21), 0)
#
#     if pre_frame is None:
#         pre_frame = gray_img
#     else:
#         img_delta = cv2.absdiff(pre_frame, gray_img)
#         thresh = cv2.threshold(img_delta, 10, 255, cv2.THRESH_BINARY)[1]
#         for i in range(2):
#             x1, y1, x2, y2 = parse_rect(res_value(f"cafe.moving_object_whitelist.{i}"))
#             thresh[y1:y2, x1:x2] = 0
#         thresh = cv2.dilate(thresh, np.ones((15, 15), np.uint8), iterations=2)
#         contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#         cur_frame = cv2.drawContours(cur_frame, contours, -1, (0, 255, 0), 2)
#         cv2.imshow('org', cur_frame)
#         cv2.imshow('img', thresh)
#         key = cv2.waitKey(30) & 0xff
#         if key == 27:
#             break
#
#         for c in contours:
#             # Calculate the moments of the contour
#             moments = cv2.moments(c)
#
#             # Calculate the centroid of the contour
#             cx = int(moments['m10'] / moments['m00'])
#             cy = int(moments['m01'] / moments['m00']) + 10
#
#             ADB.input_press_pos(cx, cy)
#
#             # if cv2.contourArea(c) < 1000:  # 设置敏感度
#             #     continue
#             # else:
#             #     # print(cv2.contourArea(c))
#             #     print("前一帧和当前帧不一样了, 有什么东西在动!")
#             #     play_music = True
#             #     break
#
#         pre_frame = gray_img
#
# cv2.destroyAllWindows()


if __name__ == '__main__':

    while True:
        mat = ADB.screencap_mat(force=True)
        for i in range(len(res_value(f"cafe.mask_neglect"))):
            x1, y1, x2, y2 = parse_rect(res_value(f"cafe.mask_neglect.{i}"))
            mat[y1:y2, x1:x2] = 0
        cv2.imshow("0", mat)
        mat = remove_res_color(mat, "cafe.color_neglect")
        cv2.imshow("1", mat)
        mat = cv2.erode(mat, np.ones((4, 4), np.uint8), iterations=2)
        cv2.imshow("2", mat)
        mat = cv2.dilate(mat, np.ones((25, 25), np.uint8), iterations=3)
        cv2.imshow("3", mat)
        gray = cv2.cvtColor(mat, cv2.COLOR_BGR2GRAY)
        contours, _ = cv2.findContours(gray.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mat = cv2.drawContours(mat, contours, -1, (0, 255, 0), 2)
        cv2.imshow("4", mat)
        for c in contours:
            # Calculate the moments of the contour
            moments = cv2.moments(c)

            xx, yy, ww, hh = cv2.boundingRect(c)

            # Calculate the centroid of the contour
            cx = int(moments['m10'] / moments['m00'])
            cy = yy + hh - 100

            # ADB.input_press_pos(cx, cy)
        cv2.waitKey(0)