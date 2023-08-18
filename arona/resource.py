import os
import typing
import cv2

import dpath
import functools

from ruamel import yaml as ruamel_yaml
from .config import get_config

resource_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), '../resources')


@functools.lru_cache()
def _get_img_path_suffix():
    hw_ratio = get_config("arona.yaml/device/resolution/width") / get_config("arona.yaml/device/resolution/height")
    return "%.2f" % hw_ratio


@functools.lru_cache()
def _get_resource_real_path(path: typing.Optional[str] = None) -> str:
    if path is not None:
        return os.path.join(resource_path, _get_img_path_suffix(), path)
    else:
        return resource_path


@functools.lru_cache()
def _load_res_yaml():
    real_path = _get_resource_real_path("res.yaml")
    with open(real_path, 'r', encoding='utf-8') as f:
        data = ruamel_yaml.load(f.read(), Loader=ruamel_yaml.RoundTripLoader)
    return data


@functools.lru_cache()
def res_value(path: str):
    path = path.replace('\\', '/')
    path = path.replace('.', '/')
    return dpath.get(_load_res_yaml(), path)


@functools.lru_cache()
def get_img(path: str, gray=False):
    real_path = _get_resource_real_path(path.replace('\\', '/').replace('.', '/'))
    real_path = real_path.replace("/png", ".png").replace("/jpg", ".jpg")
    if os.path.exists(real_path):
        pass
    elif os.path.exists(real_path + '.png'):
        real_path += '.png'
    elif os.path.exists(real_path + '.jpg'):
        real_path += '.jpg'
    else:
        raise FileNotFoundError('未能检测到图片文件.')
    if gray:
        img = cv2.imread(real_path, cv2.IMREAD_GRAYSCALE)
    else:
        img = cv2.imread(real_path)
    return img
