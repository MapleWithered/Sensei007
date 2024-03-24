
import cv2

from arona.scrcpy import ADB

if __name__ == '__main__':
    while True:
        mat = ADB.screencap_mat()
        cv2.imshow("0", mat)
        cv2.waitKey(1)


# if __name__ == '__main__':
#
#     while True:
#         mat = Scrcpy.screencap_mat(force=True)
#         for i in range(len(res_value(f"cafe.mask_neglect"))):
#             x1, y1, x2, y2 = parse_rect(res_value(f"cafe.mask_neglect.{i}"))
#             mat[y1:y2, x1:x2] = 0
#         cv2.imshow("0", mat)
#         mat = remove_res_color(mat, "cafe.color_neglect")
#         cv2.imshow("1", mat)
#         mat = cv2.erode(mat, np.ones((4, 4), np.uint8), iterations=2)
#         cv2.imshow("2", mat)
#         mat = cv2.dilate(mat, np.ones((25, 25), np.uint8), iterations=3)
#         cv2.imshow("3", mat)
#         gray = cv2.cvtColor(mat, cv2.COLOR_BGR2GRAY)
#         contours, _ = cv2.findContours(gray.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#         mat = cv2.drawContours(mat, contours, -1, (0, 255, 0), 2)
#         cv2.imshow("4", mat)
#         for c in contours:
#             # Calculate the moments of the contour
#             moments = cv2.moments(c)
#
#             xx, yy, ww, hh = cv2.boundingRect(c)
#
#             # Calculate the centroid of the contour
#             cx = int(moments['m10'] / moments['m00'])
#             cy = yy + hh - 100
#
#             # Scrcpy.input_press_pos(cx, cy)
#         cv2.waitKey(0)