import functools
import os
import typing

import dpath
from ruamel import yaml as ruamel_yaml

config_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), '../config')

yaml = ruamel_yaml.YAML(typ='rt')

@functools.lru_cache()
def _get_config_real_path(path: typing.Optional[str] = None) -> str:
    if path is not None:
        return os.path.join(config_path, path)
    else:
        return config_path


@functools.lru_cache()
def _load_config(relative_path: str):
    if not relative_path.endswith('.yaml'):
        relative_path += '.yaml'
    real_path = _get_config_real_path(relative_path)
    assert os.path.exists(real_path), real_path + '未能检测到yaml文件.'
    with open(real_path, 'r', encoding='utf-8') as f:
        data = yaml.load(f.read())
    return data


@functools.lru_cache()
def get_config(path: str):
    # slice path with .yaml, if exists.
    # first part is file name, second part is key path.
    # if .yaml not exists, throw error.
    path = path.replace('\\', '/')
    path_list = path.split('.yaml')
    if len(path_list) == 2 and path_list[1] == '':
        return _load_config(path_list[0])
    else:
        data = _load_config(path_list[0])
        return dpath.get(data, path_list[1].replace('.', '/'), default=None)


if __name__ == '__main__':
    # print(get_config("user_config.yaml"))
    # print(get_config("user_config.yaml/adb"))
    # print(get_config("user_config.yaml/adb/path"))
    pass
