import functools
import os.path
import queue
import socket
import subprocess
import time
import typing
from collections import namedtuple
from pathlib import Path

import adbutils
import cv2
import numpy as np
import scrcpy

from .. import imgops
from .. import resource as res
from ..config import get_config
from ..utils import try_until_succ

Size = namedtuple("Size", ['width', 'height'])
Pos = namedtuple("Pos", ['x', 'y'])
Rect = namedtuple("Rect", ['x1', 'y1', 'x2', 'y2'])
Color = namedtuple("Color", ['r', 'g', 'b'])


def get_adb_path() -> str:
    path = ""
    try:
        path = get_config("user_config.yaml/adb/path")
        if not os.path.exists(path):
            path = os.path.join(str(Path(__file__).parent), path)
        if not os.path.exists(path):
            path = os.path.join(os.path.join(str(Path(__file__).parent), "adb"), "adb.exe")
        if not os.path.exists(path):
            path = os.path.join(os.path.join(str(Path(__file__).parent.parent), "adb"), "adb.exe")
    except:
        path = os.path.join(os.path.join(str(Path(__file__).parent), "adb"), "adb.exe")
    return path


# Static class(?)
class ADB:
    _adb_client: adbutils.AdbClient = None
    _adb_device: adbutils.AdbDevice = None
    _scrcpy_client: scrcpy.Client = None
    _touch_dev: str = get_config("arona.yaml/device.touch.dev")

    _mat_queue: queue.Queue = queue.Queue(maxsize=1)
    _mat_prev: np.array = None
    _tapped = False

    _framerate = 10

    _loading = 1

    _loading_anchor = None
    _loading_mask = None
    _loading_template = None

    @classmethod
    def is_loading(cls):
        if not cls.adb_connected() or not cls.scrcpy_connected():
            cls.connect()
        return cls._loading > 0

    @classmethod
    def get_loading_countdown(cls):
        if not cls.adb_connected() or not cls.scrcpy_connected():
            cls.connect()
        return cls._loading

    @classmethod
    def start_adb_server(cls, host="127.0.0.1", port=5037):
        try:
            cls._adb_client.server_version()
        except:
            cls._adb_client = adbutils.AdbClient(host=host, port=port)
        try:
            return cls._adb_client.server_version()
        except:
            raise RuntimeError("ADB server failed to start")

    @classmethod
    def kill_adb_server(cls):
        cls._adb_client.server_kill()

    @classmethod
    def connect_adb_device(cls):
        device_cfg = get_config("user_config.yaml/adb.device")
        try:
            if ":" in device_cfg:
                cls._adb_client.connect(device_cfg)
                cls._adb_device = cls._adb_client.device(device_cfg)
            else:
                for dev in cls._adb_client.device_list():
                    if dev.serial == device_cfg:
                        cls._adb_device = dev
                        break
                else:
                    cls._adb_device = cls._adb_client.device()
            cls._adb_device.app_current()
            return True
        except:
            raise RuntimeError("Device not found")

    @classmethod
    def adb_connected(cls):
        try:
            cls._adb_device.app_current()
            return True
        except:
            return False

    @classmethod
    def scrcpy_connected(cls):
        return cls._scrcpy_client.alive

    @classmethod
    def connect_scrcpy(cls):
        if not cls.adb_connected():
            cls.start_adb_server()
            cls.connect_adb_device()
        bitrate = get_config("arona.yaml/scrcpy.bitrate")
        cls._framerate = get_config("arona.yaml/scrcpy.framerate")
        cls._scrcpy_client = scrcpy.Client(device=cls._adb_device, bitrate=bitrate, max_fps=cls._framerate, )
        cls._scrcpy_client.add_listener(scrcpy.EVENT_INIT, cls.listener_init)
        cls._scrcpy_client.add_listener(scrcpy.EVENT_FRAME, cls.listener_on_frame)
        cls._scrcpy_client.start(daemon_threaded=True)

    @classmethod
    def listener_init(cls):
        path_template_loading: str = res.res_value("navigation.loading")
        anchor = path_template_loading.split("-")[:4]
        anchor = [int(x) for x in anchor]  # x1, y1, x2, y2
        mat_template = res.get_img(res.res_value("navigation.loading"), unchanged=True)
        # mat_cropped: BGR, mat_template: BGRA
        # we compare the cropped mat with the template mat, using alpha channel as mask
        mask = (mat_template[:, :, 3] > 250).astype(np.uint8) * 255
        mat_template = mat_template[:, :, :3]
        # mat_template to CV8U
        mat_template = cv2.bitwise_and(mat_template, mat_template, mask=mask)
        cls._loading_anchor = anchor
        cls._loading_mask = mask
        cls._loading_template = mat_template

    @classmethod
    def listener_on_frame(cls, frame):
        if cls._loading_anchor is None:
            cls.listener_init()
        if frame is None:
            return
        mat_cropped = frame[cls._loading_anchor[1]:cls._loading_anchor[3],
                      cls._loading_anchor[0]:cls._loading_anchor[2]]
        mat_cropped = cv2.bitwise_and(mat_cropped, mat_cropped, mask=cls._loading_mask)
        match = 1 - cv2.matchTemplate(mat_cropped, cls._loading_template, cv2.TM_SQDIFF_NORMED)[0, 0]
        if match > 0.9:
            cls._loading = int(0.75 * cls._framerate)
        elif cls._loading > 0:
            cls._loading -= 1
        if not cls._mat_queue.empty():
            cls._mat_queue.get()
        if cls._tapped:
            cls._tapped = False
        cls._mat_queue.put(frame)

    @classmethod
    def connect(cls):
        try_until_succ(cls.start_adb_server)
        try:
            try_until_succ(cls.connect_adb_device)
        except:
            cls.kill_adb_server()
            cls.start_adb_server()
            cls.connect_adb_device()
        try_until_succ(cls.connect_scrcpy)

    @classmethod
    @functools.lru_cache()
    def get_resolution(cls) -> typing.Optional[Size]:
        if not cls.adb_connected() or not cls.scrcpy_connected():
            cls.connect()
        size = cls._scrcpy_client.resolution
        if size is not None:
            if size[0] > size[1]:
                long = size[0]
                short = size[1]
            else:
                long = size[1]
                short = size[0]
            return Size(int(long), int(short))
        else:
            return None

    @classmethod
    def screencap_mat(cls, force=False, allow_loading=False) -> np.array:
        if not cls.adb_connected() or not cls.scrcpy_connected():
            cls.connect()
        if not allow_loading:
            while cls._loading > 0:
                time.sleep(0.1)
        if cls._mat_prev is not None and not force:
            try:
                cls._mat_prev = cls._mat_queue.get(block=False)
            except queue.Empty:
                pass
            return cls._mat_prev
        else:
            try:
                cls._mat_prev = cls._mat_queue.get(block=True, timeout=None if force else 15)
            except queue.Empty:
                return cls._screencap_mat()
            return cls._mat_prev

    @classmethod
    def _screencap_mat(cls, std_size: bool = True, gray=False) -> np.array:
        if not cls.adb_connected() or not cls.scrcpy_connected():
            cls.connect()
        img_pil = cls._adb_device.screenshot()
        img = np.array(img_pil)
        if std_size:
            size = cls.get_resolution()
            config_height = get_config("arona.yaml/device/resolution/height")
            if config_height != size.height:
                scale_ratio = config_height / size.height
                width = int(img.shape[1] * scale_ratio)
                height = int(img.shape[0] * scale_ratio)
                dim = (width, height)
                img = cv2.resize(img, dim, cv2.INTER_LINEAR)
        if gray:
            img = imgops.mat_bgr2gray(img)
        return img

    # @classmethod
    # def screencap_pil(cls, force: bool = False, std_size: bool = False) -> PIL.Image.Image:
    #     if cls._device is None:
    #         cls.connect()
    #     img = Image.fromarray(cls.screencap_mat(force=force, std_size=std_size))
    #     return img

    @classmethod
    def get_top_activity(cls):
        if not cls.adb_connected() or not cls.scrcpy_connected():
            cls.connect()
        return cls._adb_device.app_current().activity

    @classmethod
    def input_tap(cls, x, y):
        repr_x = get_config("arona.yaml/device.touch.screen_to_touch.touch_x")
        repr_y = get_config("arona.yaml/device.touch.screen_to_touch.touch_y")

        x, y = eval(repr_x, {'x': x, 'y': y}), eval(repr_y, {'x': x, 'y': y})

        if get_config("arona.yaml/device.touch.preferred_mode") == 'adb':
            if not cls.adb_connected() or not cls.scrcpy_connected():
                cls.connect()
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 57 1")
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 1 330 1")
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 53 " + str(x))
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 54 " + str(y))
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 0 0 0")
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 57 4294967295")
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 1 330 0")
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 0 0 0")
        elif get_config("arona.yaml/device.touch.preferred_mode") == 'minitouch':
            MNT.send(f"d 0 {x} {y} 0\nc\nw 2\nu 0\nc\nw 2\n")
        cls._mat_prev = None
        cls._tapped = True

    @classmethod
    def input_press_down(cls, x, y, idx=0):
        repr_x = get_config("arona.yaml/device.touch.screen_to_touch.touch_x")
        repr_y = get_config("arona.yaml/device.touch.screen_to_touch.touch_y")

        x, y = eval(repr_x, {'x': x, 'y': y}), eval(repr_y, {'x': x, 'y': y})

        if get_config("arona.yaml/device.touch.preferred_mode") == 'adb':
            if not cls.adb_connected() or not cls.scrcpy_connected():
                cls.connect()
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 57 1")
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 1 330 1")
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 53 " + str(x))
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 54 " + str(y))
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 0 0 0")
        elif get_config("arona.yaml/device.touch.preferred_mode") == 'minitouch':
            MNT.send(f"d {idx} {x} {y} 0\nc\nw 2\n")
        cls._mat_prev = None
        cls._tapped = True

    @classmethod
    def input_press_up(cls, idx=0):
        if get_config("arona.yaml/device.touch.preferred_mode") == 'adb':
            if not cls.adb_connected() or not cls.scrcpy_connected():
                cls.connect()
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 57 4294967295")
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 1 330 0")
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 0 0 0")
        elif get_config("arona.yaml/device.touch.preferred_mode") == 'minitouch':
            MNT.send(f"u {idx}\nc\nw 2\n")
        cls._mat_prev = None
        cls._tapped = True

    @classmethod
    def input_press_move(cls, x, y, idx=0):
        repr_x = get_config("arona.yaml/device.touch.screen_to_touch.touch_x")
        repr_y = get_config("arona.yaml/device.touch.screen_to_touch.touch_y")

        x, y = eval(repr_x, {'x': x, 'y': y}), eval(repr_y, {'x': x, 'y': y})

        if get_config("arona.yaml/device.touch.preferred_mode") == 'adb':
            raise NotImplementedError("Move not implemented for ADB, TODO")
        elif get_config("arona.yaml/device.touch.preferred_mode") == 'minitouch':
            MNT.send(f"m {idx} {x} {y} 0\nc\nw 2\n")
        cls._mat_prev = None
        cls._tapped = True

    @classmethod
    def input_swipe(cls, start_x, start_y, end_x, end_y, duration_ms, hold_time_ms=100):
        repr_x = get_config("arona.yaml/device.touch.screen_to_touch.touch_x")
        repr_y = get_config("arona.yaml/device.touch.screen_to_touch.touch_y")

        def converter(x, y):
            return eval(repr_x, {'x': x, 'y': y}), eval(repr_y, {'x': x, 'y': y})

        start_x, start_y = converter(start_x, start_y)
        end_x, end_y = converter(end_x, end_y)

        if get_config("arona.yaml/device.touch.preferred_mode") == 'adb':
            if not cls.adb_connected() or not cls.scrcpy_connected():
                cls.connect()

            # get ms time
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 57 1")
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 1 330 1")
            time_start = int(round(time.time() * 1000))
            while time.time() * 1000 - time_start < duration_ms:
                cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 53 " + str(int(start_x + (end_x - start_x) * (
                        time.time() * 1000 - time_start) / duration_ms)))
                cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 54 " + str(int(start_y + (end_y - start_y) * (
                        time.time() * 1000 - time_start) / duration_ms)))
                cls._adb_device.shell(f"sendevent {cls._touch_dev} 0 0 0")
                # time.sleep(0.01)
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 53 " + str(int(end_x)))
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 54 " + str(int(end_y)))
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 0 0 0")
            time.sleep(hold_time_ms / 1000)
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 3 57 4294967295")
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 1 330 0")
            cls._adb_device.shell(f"sendevent {cls._touch_dev} 0 0 0")
        elif get_config("arona.yaml/device.touch.preferred_mode") == 'minitouch':
            MNT.send(f"d 0 {start_x} {start_y} 0\nc\nw 2\n")
            # get ms time
            time_start = int(round(time.time() * 1000))
            while time.time() * 1000 - time_start < duration_ms:
                MNT.send(
                    f"m 0 {int(start_x + (end_x - start_x) * (time.time() * 1000 - time_start) / duration_ms)} {int(start_y + (end_y - start_y) * (time.time() * 1000 - time_start) / duration_ms)} 0\nc\nw 2\n")
                time.sleep(0.01)
            MNT.send(f"m 0 {end_x} {end_y} 0\nc\nw 2\n")
            time.sleep(hold_time_ms / 1000)
            MNT.send(f"u 0\nc\nw 2\n")
        cls._mat_prev = None
        cls._tapped = True

    @classmethod
    def input_zoom(cls, finger1=None, finger2=None, duration_ms=500, hold_time_ms=200):
        # finger1: [start_x, start_y, end_x, end_y]
        # finger2: [start_x, start_y, end_x, end_y]
        if finger2 is None:
            finger2 = [1246, 576, 1042, 576]
        if finger1 is None:
            finger1 = [766, 576, 968, 576]
        repr_x = get_config("arona.yaml/device.touch.screen_to_touch.touch_x")
        repr_y = get_config("arona.yaml/device.touch.screen_to_touch.touch_y")

        def converter(x, y):
            return eval(repr_x, {'x': x, 'y': y}), eval(repr_y, {'x': x, 'y': y})

        start_x0, start_y0 = converter(finger1[0], finger1[1])
        end_x0, end_y0 = converter(finger1[2], finger1[3])
        start_x1, start_y1 = converter(finger2[0], finger2[1])
        end_x1, end_y1 = converter(finger2[2], finger2[3])

        if get_config("arona.yaml/device.touch.preferred_mode") == 'adb':
            raise NotImplementedError("Zoom not implemented for ADB")
        elif get_config("arona.yaml/device.touch.preferred_mode") == 'minitouch':
            MNT.send(f"d 0 {start_x0} {start_y0} 0\nd 1 {start_x1} {start_y1} 0\nc\nw 2\n")
            # get ms time
            time_start = int(round(time.time() * 1000))
            while time.time() * 1000 - time_start < duration_ms:
                MNT.send(
                    f"m 0 {int(start_x0 + (end_x0 - start_x0) * (time.time() * 1000 - time_start) / duration_ms)} {int(start_y0 + (end_y0 - start_y0) * (time.time() * 1000 - time_start) / duration_ms)} 0\n"
                    + f"m 1 {int(start_x1 + (end_x1 - start_x1) * (time.time() * 1000 - time_start) / duration_ms)} {int(start_y1 + (end_y1 - start_y1) * (time.time() * 1000 - time_start) / duration_ms)} 0\nc\nw 2\n")
                time.sleep(0.01)
            MNT.send(f"m 0 {end_x0} {end_y0} 0\nm 1 {end_x1} {end_y1} 0\nc\nw 2\n")
            time.sleep(hold_time_ms / 1000)
            MNT.send(f"u 0\nu 1\nc\nw 2\n")
        cls._mat_prev = None
        cls._tapped = True

    @classmethod
    def input_press_pos(cls, x, y):
        cls.input_tap(x, y)

    @classmethod
    def input_press_rect(cls, x1, y1, x2, y2):
        cls.input_tap(int((x1 + x2) / 2), int((y1 + y2) / 2))

    @classmethod
    def input_swipe_pos(cls, pos1: Pos, pos2: Pos, duration_ms: int, hold_time_ms=100):
        cls.input_swipe(int(pos1.x), int(pos1.y), int(pos2.x), int(pos2.y), duration_ms, hold_time_ms)

    @classmethod
    def get_device_object(cls):
        if not cls.adb_connected():
            cls.connect()
        return cls._adb_device


def is_port_open(port):
    try:
        # Create a socket object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set a timeout of 1 second
        sock.settimeout(1)
        # Try to connect to the specified port
        result = sock.connect_ex(('localhost', port))
        # If the result is 0, the port is open; otherwise, it's closed or unreachable
        return result == 0
    except socket.error as e:
        print(f"Error occurred while checking port {port}: {e}")
        return False
    finally:
        # Close the socket
        sock.close()


# Minicap
class MNT:
    _port = 0
    _sock = None

    @classmethod
    def init_device(cls, port=16380):

        if cls._sock:
            return

        if ADB.get_device_object().shell("pgrep minitouch") == "":
            cls._port = port

            abi: str = ADB.get_device_object().shell('getprop ro.product.cpu.abi').strip()
            sdk: int = int(ADB.get_device_object().shell('getprop ro.build.version.sdk').strip())
            pre: str = ADB.get_device_object().shell('getprop ro.build.version.preview_sdk').strip()
            rel: str = ADB.get_device_object().shell('getprop ro.build.version.release').strip()

            if pre and int(pre) > 0:
                sdk += 1

            # LD_LIBRARY_PATH=/data/local/tmp/minicap-devel exec /data/local/tmp/minicap-devel/minicap -P 1920x1080@1920x1080/0 -s

            # PIE is only supported since SDK 16
            if sdk >= 16:
                bin = "minitouch"
            else:
                bin = "minitouch-nopie"

            dir = "/data/local/tmp"
            ADB.get_device_object().shell(f'mkdir {dir} 2>/dev/null || true')

            basepath = get_adb_path()
            basepath = basepath[:basepath.rfind(os.path.sep)]  # remove adb.exe from basepath
            basepath = os.path.join(basepath, "minitouch")

            # Push minicap binary
            ADB.get_device_object().push(f'{basepath}/{abi}/bin/{bin}', f'{dir}/{bin}')

            ADB.get_device_object().shell(f'chmod 777 {dir}/{bin}')

            # Start minicap & forwarding
            res = subprocess.Popen(
                [get_adb_path(), 'shell', '/data/local/tmp/minitouch'], stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            while res.poll() is None:
                line = res.stdout.readline().decode("utf8")
                # if line.strip() != "":
                #     print("log", line)
                if "detected" in line:
                    break

        if not is_port_open(port):
            subprocess.run([get_adb_path(), 'forward', f'tcp:{port}', f'localabstract:minitouch'],
                           stdout=subprocess.PIPE)

        cls._port = port
        cls._sock = socket.create_connection(("localhost", cls._port), timeout=3)

        time_start = time.time()
        while time.time() < time_start + 3:
            if 'v' in cls._sock.recv(1024).decode("utf8"):
                return

        print("MNT init failed")
        return

    @classmethod
    def send(cls, cmd):
        if not cls._sock:
            cls.init_device()
        try:
            cls._sock.sendall(cmd.encode("utf8"))
        except:
            cls._sock = None
            cls.init_device()
            cls._sock.sendall(cmd.encode("utf8"))

#
# # Minicap
# class MNC:
#     _port = 0
#
#     @classmethod
#     def connect(cls):
#         ...
#
#     @classmethod
#     def init_device(cls, port=16380):
#
#         if cls._port != 0:
#             return
#         if is_port_open(port):
#             cls._port = port
#             return
#
#         cls._port = 16380
#
#         abi: str = Scrcpy.get_adb_device_object().shell('getprop ro.product.cpu.abi').strip()
#         sdk: int = int(Scrcpy.get_adb_device_object().shell('getprop ro.build.version.sdk').strip())
#         pre: str = Scrcpy.get_adb_device_object().shell('getprop ro.build.version.preview_sdk').strip()
#         rel: str = Scrcpy.get_adb_device_object().shell('getprop ro.build.version.release').strip()
#
#         if pre and int(pre) > 0:
#             sdk += 1
#
#         if sdk > 30:
#             sdk = 30
#         # LD_LIBRARY_PATH=/data/local/tmp/minicap-devel exec /data/local/tmp/minicap-devel/minicap -P 1920x1080@1920x1080/0 -s
#
#         # PIE is only supported since SDK 16
#         if sdk >= 16:
#             bin = "minicap"
#         else:
#             bin = "minicap-nopie"
#
#         dir = "/data/local/tmp/minicap-devel"
#         Scrcpy.get_adb_device_object().shell(f'mkdir {dir} 2>/dev/null || true')
#
#         basepath = get_adb_path()
#         basepath = basepath[:basepath.rfind(os.path.sep)]  # remove adb.exe from basepath
#         basepath = os.path.join(basepath, "minicap")
#
#         # Push minicap binary
#         Scrcpy.get_adb_device_object().push(f'{basepath}/{abi}/bin/{bin}', f'{dir}/{bin}')
#         Scrcpy.get_adb_device_object().push(f'{basepath}/libs/android-{sdk}/{abi}/minicap.so', f'{dir}/minicap.so')
#
#         Scrcpy.get_adb_device_object().shell(f'chmod 777 {dir}/{bin} {dir}/{bin}.so')
#
#         # Start minicap & forwarding
#         res = subprocess.Popen(
#             [get_adb_path(), 'shell', f'LD_LIBRARY_PATH={dir}', "exec", f'{dir}/{bin}', '-P',
#              '1920x1080@1920x1080/0'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#         while res.poll() is None:
#             line = res.stdout.readline().decode("utf8")
#             if line.strip() != "":
#                 print("log", line)
#             if "Publishing virtual display" in line:
#                 break
#
#     @classmethod
#     def bind_port(cls, port):
#         subprocess.run(
#             [get_adb_path(), 'forward', f'tcp:{port}', f'localabstract:minicap'], stdout=subprocess.PIPE)
#
#     @classmethod
#     def _read_bytes(self, socket, length):
#         data = bytearray()
#         while length > 0:
#             tmp = socket.recv(length)
#             length -= len(tmp)
#             data.extend(tmp)
#         return bytearray(data)
#
#     @classmethod
#     def capture(cls):
#         if cls._port == 0:
#             cls.init_device()
#         assert is_port_open(cls._port)
#         sock = socket.create_connection(("127.0.0.1", cls._port), timeout=3)
#         version = cls._read_bytes(sock, 1)[0]
#         print("Version {}".format(version))
#         banner_length = cls._read_bytes(sock, 1)[0]
#         banner_rest = cls._read_bytes(sock, banner_length - 2)
#         print("Banner length {}".format(banner_length))
#         frame_bytes = cls._read_bytes(socket, 4)
#         total = int.from_bytes(frame_bytes, byteorder="little")
#         print("JPEG data: {}".format(total))
#         jpeg_data = cls._read_bytes(socket, total)
#         sock.close()
#
#
# if __name__ == '__main__':
#     ADB.kill_adb_server()
#     MNC.init_device()
#     # MNC.bind_port(16380)
#     # MNC.capture()
