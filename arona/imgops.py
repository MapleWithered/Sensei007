from collections import namedtuple

import PIL.Image
import cv2
import numpy
import numpy as np


Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])


def pil_to_mat(pil_img: PIL.Image.Image):
    mat = numpy.array(pil_img).copy()
    # mat = mat[:, :, ::-1].copy()
    return mat


def mat_crop(mat, rect: Rect):
    return mat[int(rect.y1):int(rect.y2), int(rect.x1):int(rect.x2)].copy()


def from_percent_pos(res: Size, pos: Pos) -> Pos:
    return Pos(int(pos.x / 100 * res.width),
               int(pos.y / 100 * res.height))


def from_percent_rect(res: Size, rect: Rect) -> Rect:
    return Rect(int(rect.x1 / 100 * res.width),
                int(rect.y1 / 100 * res.height),
                int(rect.x2 / 100 * res.width),
                int(rect.y2 / 100 * res.height))


def from_std_pos(res: Size, pos: Pos) -> Pos:
    return Pos(int(pos.x / 1080 * res.height),
               int(pos.y / 1080 * res.height))


def from_std_rect(res: Size, rect: Rect) -> Rect:
    return Rect(int(rect.x1 / 1080 * res.height),
                int(rect.y1 / 1080 * res.height),
                int(rect.x2 / 1080 * res.height),
                int(rect.y2 / 1080 * res.height))


def mat_bgr2gray(mat):
    return cv2.cvtColor(mat, cv2.COLOR_BGR2GRAY)


def mat_pick_color_hsv(mat, hsv: Color, tolerance: Color = Color(4, 4, 8)):
    low_color = np.array([int(hsv.r / 2 - tolerance.r / 2), int(hsv.g * 2.55 - tolerance.g * 2.55),
                          int(hsv.b * 2.55 - tolerance.b * 2.55)])
    high_color = np.array([int(hsv.r / 2 + tolerance.r / 2), int(hsv.g * 2.55 + tolerance.g * 2.55),
                           int(hsv.b * 2.55 + tolerance.b * 2.55)])
    mask = cv2.inRange(mat, low_color, high_color)
    res = cv2.bitwise_and(mat, mat, mask=mask)
    return res


def mat_pick_color_rgb(mat, rgb: Color, tolerance=3):
    low_color = np.array([rgb.b - tolerance, rgb.g - tolerance, rgb.r - tolerance])
    high_color = np.array([rgb.b + tolerance, rgb.g + tolerance, rgb.r + tolerance])
    mask = cv2.inRange(mat, low_color, high_color)
    res = cv2.bitwise_and(mat, mat, mask=mask)
    return res


def mat_pick_grey(mat, light: int, tolerance=3):
    low_color = light - tolerance
    high_color = light + tolerance
    mask = cv2.inRange(mat, low_color, high_color)
    res = cv2.bitwise_and(mat, mat, mask=mask)
    return res


def mat_threshold(mat, threshold):
    return cv2.threshold(mat, threshold, 255, cv2.THRESH_BINARY)[1]


def uniform_size(mat1, mat2):
    if mat1.size[0] < mat2.size[0]:
        return mat1, cv2.resize(mat2, mat1.size, cv2.INTER_LINEAR)
    elif mat1.size[0] > mat2.size[0]:
        return cv2.resize(mat1, mat2.size, cv2.INTER_LINEAR), mat2
    elif mat1.size[1] != mat2.size[1]:
        return cv2.resize(mat1, mat2.size, cv2.INTER_LINEAR), mat2
    else:
        return mat1, mat2


def save_image(mat, filepath):
    cv2.imwrite(filepath, mat)
