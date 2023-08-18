import math
from collections import namedtuple

import cv2
import numpy as np
from matplotlib import pyplot as plt

from . import imgops

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])

RectResult = namedtuple("RectResult", ['rect', 'val'])


def match_template(screenshot, template):
    ...


def match_masked_template_best(img, template, mask, method=cv2.TM_CCOEFF_NORMED, show_result=False):
    assert template.shape == mask.shape
    mask = mask.copy()
    mask = mask.astype(np.float32)
    mask /= 255.0
    # Apply template Matching
    res = cv2.matchTemplate(img, templ=template, method=method, mask=mask)
    res[np.logical_or(np.isinf(res), np.isnan(res))] = (1 if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED] else 0)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
        val = min_val
    else:
        top_left = max_loc
        val = max_val
    bottom_right = (top_left[0] + template.shape[1::-1][0], top_left[1] + template.shape[1::-1][1])

    if show_result:
        res_img = img.copy()
        if len(res_img.shape) == 2:
            res_img = cv2.cvtColor(res_img, cv2.COLOR_GRAY2BGR)
        cv2.rectangle(res_img, top_left, bottom_right, (255, 0, 0), 5)

        plt.subplot(121), plt.imshow(res, cmap='gray')
        plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
        plt.subplot(122), plt.imshow(res_img)
        plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
        plt.suptitle("Match template result")

        plt.show()

    return RectResult(Rect(top_left[0], top_left[1], bottom_right[0], bottom_right[1]), val)


def match_template_best(img, template, method=cv2.TM_SQDIFF_NORMED, show_result=False) -> RectResult:
    # Apply template Matching
    res = cv2.matchTemplate(img, templ=template, method=method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
        val = min_val
    else:
        top_left = max_loc
        val = max_val
    bottom_right = (top_left[0] + template.shape[::-1][-2], top_left[1] + template.shape[::-1][-1])

    if show_result:
        res_img = img.copy()
        res_img = cv2.cvtColor(res_img, cv2.COLOR_GRAY2BGR)
        cv2.rectangle(res_img, top_left, bottom_right, (255, 0, 0), 5)

        plt.subplot(121), plt.imshow(res, cmap='gray')
        plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
        plt.subplot(122), plt.imshow(res_img)
        plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
        plt.suptitle("Match template result")

        plt.show()

    return RectResult(Rect(top_left[0], top_left[1], bottom_right[0], bottom_right[1]), val)


def match_template_all(img_gray, template, mask=None, method=cv2.TM_CCOEFF_NORMED, score_threshold=0.82,
                       show_result=False, group_rectangle=1):
    w, h = template.shape[:2][::-1]
    res = cv2.matchTemplate(img_gray, template, method=method, mask=mask)
    for i in range(res.shape[0]):
        for j in range(res.shape[1]):
            if math.isinf(res[i][j]) or math.isnan(res[i][j]):
                res[i][j] = 0
    if show_result:
        plt.imshow(res)
        plt.show()
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        loc = np.where(res <= score_threshold)
    else:
        loc = np.where(res >= score_threshold)
    img_temp = img_gray.copy()
    if len(template.shape) == 2:
        img_temp = cv2.cvtColor(img_temp, cv2.COLOR_GRAY2BGR)
    result_list: list[RectResult] = []
    rectangle_list: list = []
    for pt in zip(*loc[::-1]):
        rectangle_list.append([pt[0], pt[1], pt[0] + w, pt[1] + h])
    result = cv2.groupRectangles(rectangle_list, group_rectangle)
    for rect in result[0]:
        if show_result:
            cv2.rectangle(img_temp, (rect[0], rect[1]), (rect[2], rect[3]), (255, 0, 0), 5)
        result_list.append(RectResult(Rect(*list(rect)), res[rect[1], rect[0]]))
    if show_result:
        plt.imshow(img_temp)
        plt.show()
    return result_list


def compare_mat(img1, img2):
    temp1 = np.asarray(img1)
    temp2 = np.asarray(img2)
    if not img1.shape == img2.shape:
        temp1, temp2 = imgops.uniform_size(img1, img2)
    result = cv2.matchTemplate(temp1, temp2, cv2.TM_CCOEFF_NORMED)[0, 0]
    return result
