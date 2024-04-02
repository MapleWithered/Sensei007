import time

import numpy as np
from ruamel import yaml as ruamel_yaml

from arona.adb import MNT, ADB
from arona.imgreco import match_res
from arona.presser import wait_n_press_res

yaml = ruamel_yaml.YAML(typ='rt')

if __name__ == '__main__':

    print()
    print("初始化ADB与MNT")
    MNT.init_device()
    assert match_res("mini_game.cover.summer_bounce") or match_res("mini_game.cover.colorful_beach"), "请从小游戏主页运行脚本"
    assert match_res("mini_game.start_btn"), "当前难度未解锁"
    map_path: str
    if match_res("mini_game.cover.summer_bounce"):
        if match_res("mini_game.cover.normal_chosen"):
            map_path = "normal.yaml"
        elif match_res("mini_game.cover.hard_chosen"):
            map_path = "hard.yaml"
        elif match_res("mini_game.cover.veryhard_chosen"):
            map_path = "veryhard.yaml"
        else:
            map_path = ""
    elif match_res("mini_game.cover.colorful_beach"):
        map_path = "special.yaml"
    else:
        map_path = ""
    assert map_path != "", "未匹配到关卡"
    with open(map_path, 'r', encoding='utf-8') as f:
        data = yaml.load(f.read())
        map_notes = data['notes']
        unit_time = data['unit']
    map_notes = [(str(i).split(', ')[0], float(str(i).split(', ')[1]) * unit_time) for i in map_notes]

    print("使用谱面", map_path)

    wait_n_press_res("mini_game.start_btn")
    print("开始游戏，等待初始音符出现")

    ADB._cap_daemon_run = False


    def color_in_range(color: list, color_std: list, tolerance: list):
        for i in range(3):
            if abs(color[i] - color_std[i]) > tolerance[i]:
                return False
        return True


    while True:
        new_mat = np.zeros((100, 1920 - 714, 3), dtype=np.uint8)
        result = np.zeros((100, 1920 - 714, 3), dtype=np.uint8)
        time_screenshot = time.time()
        mat = ADB._screencap_mat(False, False)
        # print("screenshot time:", time.time() - time_screenshot)
        XXX = np.linspace(714, 1920, 1920 - 714, endpoint=False)
        YYY = -312 / 1337 * XXX + 595
        for x in XXX:
            y = YYY[int(x - 714)]
            color = mat[int(y), int(x), :]
            if color_in_range(color, [3, 190, 226], [46, 20, 20]):  # yellow, left
                result[:, int(x - 714), :] = [3, 190, 226]
            elif color_in_range(color, [186, 196, 57], [30, 15, 15]):  # blue, right
                result[:, int(x - 714), :] = [186, 196, 57]
            elif color_in_range(color, [214, 109, 202], [15, 15, 15]):  # blue, right
                result[:, int(x - 714), :] = [214, 109, 202]
            # 90bpm, 1beat=376px=667ms
            new_mat[:, int(x - 714), :] = mat[int(y), int(x), :]

        first_note = 0
        for x in XXX:
            if result[0, int(x - 714), 0] != 0:
                first_note = x - 714
                print("发现第一击音符")
                break

        if first_note != 0:
            break

    time_first_note = 0.0024 * first_note + 0.1 + time_screenshot

    time_next_note = time_first_note

    print("第一击时间戳: ", time_first_note, "，准备打击")
    while time.time() < time_first_note:
        pass

    for key, time_after in map_notes:
        while time.time() < time_next_note:
            pass
        match key:
            case 'L':
                ADB.input_press_pos(200, 540)
            case 'R':
                ADB.input_press_pos(1800, 540)
            case 'Ld':
                ADB.input_press_down(200, 540)
            case 'Lu':
                ADB.input_press_up()
            case 'Rd':
                ADB.input_press_down(1800, 540)
            case 'Ru':
                ADB.input_press_up()
            case 'LR':
                ADB.input_press_down(200, 540, 0)
                ADB.input_press_down(1800, 540, 1)
                time.sleep(0.01)
                ADB.input_press_up(0)
                ADB.input_press_up(1)
            case 'LRd':
                ADB.input_press_down(200, 540, 0)
                ADB.input_press_down(1800, 540, 1)
            case 'LRu':
                ADB.input_press_up(0)
                ADB.input_press_up(1)
            case 'L^':
                ADB.input_swipe(200, 540, 200, 440, 80, 0)
            case 'R^':
                ADB.input_swipe(1800, 540, 1800, 440, 80, 0)

        time_next_note += time_after

    exit(0)

    # cv2.imshow("res", result)
    # cv2.waitKey(1)
