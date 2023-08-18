import numpy as np
from . import resource as res
from .adb import ADB
import cv2
from . import imgops


def find_res(res_path: str, threshold: float = 0.995, norm=False):
    mat_template = res.get_img(res.res_value(res_path))
    mat_screen = ADB.screencap_mat()

    if norm:
        method = cv2.TM_SQDIFF
    else:
        method = cv2.TM_SQDIFF_NORMED

    # Apply template Matching
    result = cv2.matchTemplate(mat_screen, templ=mat_template, method=method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
        val = 1 - min_val
    else:
        top_left = max_loc
        val = max_val
    bottom_right = (top_left[0] + mat_template.shape[::-1][-2], top_left[1] + mat_template.shape[::-1][-1])
    return val > threshold, top_left[0], top_left[1], bottom_right[0], bottom_right[1], val
    # if show_result:
    #     res_img = img.copy()
    #     res_img = cv2.cvtColor(res_img, cv2.COLOR_GRAY2BGR)
    #     cv2.rectangle(res_img, top_left, bottom_right, (255, 0, 0), 5)
    #
    #     plt.subplot(121), plt.imshow(res, cmap='gray')
    #     plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
    #     plt.subplot(122), plt.imshow(res_img)
    #     plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
    #     plt.suptitle("Match template result")
    #
    #     plt.show()
    #
    # return RectResult(Rect(top_left[0], top_left[1], bottom_right[0], bottom_right[1]), val)


def match_file(path: str, threshold: float = 0.96) -> bool:
    file_name = path.split('/')[-1]
    # file_name be like x1-y1-x2-y2-time.png
    x1, y1, x2, y2 = file_name.split('-')[:4]
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    mat_template = res.get_img(path)
    mat_screen = ADB.screencap_mat()[y1:y2, x1:x2]
    result = compare_mat(mat_template, mat_screen)
    # cv2.imshow("1", mat_template)
    # cv2.imshow("2", mat_screen)
    # print(result)
    # cv2.waitKey(0)
    return result > threshold


def match_res(res_path: str, threshold: float = 0.96, strict=False) -> bool:
    path = res.res_value(res_path)
    return match_file(path, threshold)


def compare_mat(img1, img2, strict=False):
    temp1 = np.asarray(img1)
    temp2 = np.asarray(img2)
    if not img1.shape == img2.shape:
        temp1, temp2 = imgops.uniform_size(img1, img2)
    if not strict:
        result = 1 - cv2.matchTemplate(temp1, temp2, cv2.TM_SQDIFF_NORMED)[0, 0]
    else:
        result = 1 - cv2.matchTemplate(temp1, temp2, cv2.TM_SQDIFF)[0, 0]
    return result
