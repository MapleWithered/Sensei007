import functools
import os.path
import socket
import subprocess
import time
import typing
import threading
import queue
from collections import namedtuple
from pathlib import Path

import PIL
import cv2
import numpy as np
import ppadb.device
import pyminitouch
from PIL import Image
from ppadb.client import Client

from . import imgops
from .config import get_config
from . import resource as res

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


pyminitouch.connection.config.ADB_EXECUTOR = get_adb_path()
pyminitouch.connection._ADB = pyminitouch.connection.config.ADB_EXECUTOR


def get_adb_device() -> str:
    return get_config("user_config.yaml/adb/device")


# Static class(?)
class ADB:
    _device: ppadb.device.Device = None
    _touch_dev: str = get_config("arona.yaml/device.touch.dev")

    _mat_queue: queue.Queue = queue.Queue(maxsize=1)
    _cap_daemon_run = False
    _cap_daemon_thread = None
    _mat_prev: np.array = None
    _tapped = False

    _loading = 1

    @classmethod
    def screencap_daemon(cls):
        cls._cap_daemon_run = True
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
        try:
            while cls._cap_daemon_run:
                mat = cls._screencap_mat()
                mat_cropped = mat[anchor[1]:anchor[3], anchor[0]:anchor[2]]
                mat_cropped = cv2.bitwise_and(mat_cropped, mat_cropped, mask=mask)
                match = 1 - cv2.matchTemplate(mat_cropped, mat_template, cv2.TM_SQDIFF_NORMED)[0, 0]
                if match > 0.9:
                    cls._loading = 3
                elif cls._loading > 0:
                    cls._loading -= 1
                if not cls._mat_queue.empty():
                    cls._mat_queue.get()
                if cls._tapped:
                    cls._tapped = False
                    continue
                cls._mat_queue.put(mat)
        except KeyboardInterrupt:
            return

    @classmethod
    def is_loading(cls):
        if cls._device is None:
            cls.connect()
        if not cls._cap_daemon_run:
            cls._cap_daemon_thread = threading.Thread(target=cls.screencap_daemon)
            cls._cap_daemon_run = True
            cls._cap_daemon_thread.start()
        return cls._loading > 0

    @classmethod
    def get_loading_countdown(cls):
        if cls._device is None:
            cls.connect()
        if not cls._cap_daemon_run:
            cls._cap_daemon_thread = threading.Thread(target=cls.screencap_daemon)
            cls._cap_daemon_run = True
            cls._cap_daemon_thread.start()
        return cls._loading

    @classmethod
    def start_adb_server(cls):
        p = subprocess.Popen([get_adb_path(), 'start-server'])
        while p.wait():
            time.sleep(0.5)

    @classmethod
    def kill_adb_server(cls):
        p = subprocess.Popen([get_adb_path(), 'kill-server'])
        while p.wait():
            time.sleep(0.5)

    @classmethod
    def start_adb_client(cls, host: str = "127.0.0.1", port: int = 5037) -> Client:
        client = Client(host, port)
        try:
            client.version()  # 尝试进行实际通讯
        except RuntimeError:
            cls.start_adb_server()
            client = Client(host, port)
            client.version()
        return client

    @classmethod
    def connect(cls):
        client = cls.start_adb_client()

        device_name = get_adb_device()
        # if device is IP:addr
        if device_name.find(":") != -1:
            host, port = device_name.split(":")
            assert client.remote_connect(host, int(port))

        for dev in client.devices():
            if dev.serial == device_name:
                cls._device = dev
                break
        else:
            raise RuntimeError("Device not found")

        if not cls._cap_daemon_run:
            cls._cap_daemon_thread = threading.Thread(target=cls.screencap_daemon)
            cls._cap_daemon_run = True
            cls._cap_daemon_thread.start()

    @classmethod
    @functools.lru_cache()
    def get_resolution(cls) -> typing.Optional[Size]:
        if cls._device is None:
            cls.connect()
        size = cls._device.wm_size()
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
    def _screencap_raw(cls) -> str:
        # cat /proc/net/arp | grep :    -> NcAddress
        screenshot_ttl = 0.2
        if cls._device is None:
            cls.connect()
        error_counter = 0
        while error_counter < 5:
            try:
                img = cls._device.screencap()
                return img
            except RuntimeError:
                print("ADB FAILURE, restarting ADB server...")
                ADB.kill_adb_server()
                ADB.start_adb_server()
                cls.connect()
                error_counter += 1
                continue
        raise RuntimeError("ADB FAILURE")
        # if time.monotonic() - cls._prev_screenshot_timestamp > screenshot_ttl or force:
        #     cls._prev_screenshot_raw = cls._device.screencap()
        #     cls._prev_screenshot_timestamp = time.monotonic()
        #     return cls._prev_screenshot_raw
        # else:
        #     return cls._prev_screenshot_raw

    @classmethod
    def screencap_mat(cls, force=False, allow_loading=False) -> np.array:
        if cls._device is None:
            cls.connect()
        if not cls._cap_daemon_run:
            cls._cap_daemon_thread = threading.Thread(target=cls.screencap_daemon)
            cls._cap_daemon_run = True
            cls._cap_daemon_thread.start()
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
                cls._mat_prev = cls._mat_queue.get(block=True, timeout=None if force else 4)
            except queue.Empty:
                return cls._screencap_mat()
            return cls._mat_prev

    @classmethod
    def _screencap_mat(cls, std_size: bool = True, gray=False) -> np.array:
        if cls._device is None:
            cls.connect()
        img_np = np.frombuffer(cls._screencap_raw(), dtype=np.uint8)
        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
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
        if cls._device is None:
            cls.connect()
        return cls._device.get_top_activity()

    @classmethod
    def input_text(cls, string: str):
        if cls._device is None:
            cls.connect()
        return cls._device.input_text(string)

    @classmethod
    def input_keyevent(cls, keycode, long_press=False):
        if cls._device is None:
            cls.connect()
        return cls._device.input_keyevent(keycode, long_press)

    @classmethod
    def input_tap(cls, x, y):
        repr_x = get_config("arona.yaml/device.touch.screen_to_touch.touch_x")
        repr_y = get_config("arona.yaml/device.touch.screen_to_touch.touch_y")

        x, y = eval(repr_x, {'x': x, 'y': y}), eval(repr_y, {'x': x, 'y': y})

        if get_config("arona.yaml/device.touch.preferred_mode") == 'adb':
            if cls._device is None:
                cls.connect()
            cls._device.shell(f"sendevent {cls._touch_dev} 3 57 1")
            cls._device.shell(f"sendevent {cls._touch_dev} 1 330 1")
            cls._device.shell(f"sendevent {cls._touch_dev} 3 53 " + str(x))
            cls._device.shell(f"sendevent {cls._touch_dev} 3 54 " + str(y))
            cls._device.shell(f"sendevent {cls._touch_dev} 0 0 0")
            cls._device.shell(f"sendevent {cls._touch_dev} 3 57 4294967295")
            cls._device.shell(f"sendevent {cls._touch_dev} 1 330 0")
            cls._device.shell(f"sendevent {cls._touch_dev} 0 0 0")
        elif get_config("arona.yaml/device.touch.preferred_mode") == 'minitouch':
            MNT.send(f"d 0 {x} {y} 0\nc\nw 2\nu 0\nc\nw 2\n")
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
            if cls._device is None:
                cls.connect()

            # get ms time
            cls._device.shell(f"sendevent {cls._touch_dev} 3 57 1")
            cls._device.shell(f"sendevent {cls._touch_dev} 1 330 1")
            time_start = int(round(time.time() * 1000))
            while time.time() * 1000 - time_start < duration_ms:
                cls._device.shell(f"sendevent {cls._touch_dev} 3 53 " + str(int(start_x + (end_x - start_x) * (
                        time.time() * 1000 - time_start) / duration_ms)))
                cls._device.shell(f"sendevent {cls._touch_dev} 3 54 " + str(int(start_y + (end_y - start_y) * (
                        time.time() * 1000 - time_start) / duration_ms)))
                cls._device.shell(f"sendevent {cls._touch_dev} 0 0 0")
                # time.sleep(0.01)
            cls._device.shell(f"sendevent {cls._touch_dev} 3 53 " + str(int(end_x)))
            cls._device.shell(f"sendevent {cls._touch_dev} 3 54 " + str(int(end_y)))
            cls._device.shell(f"sendevent {cls._touch_dev} 0 0 0")
            time.sleep(hold_time_ms / 1000)
            cls._device.shell(f"sendevent {cls._touch_dev} 3 57 4294967295")
            cls._device.shell(f"sendevent {cls._touch_dev} 1 330 0")
            cls._device.shell(f"sendevent {cls._touch_dev} 0 0 0")
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
    def input_roll(cls, dx, dy):
        if cls._device is None:
            cls.connect()
        return cls._device.input_roll(dx, dy)

    @classmethod
    def create_connection(cls):
        if cls._device is None:
            cls.connect()
        conn = cls._device.create_connection()
        return conn

    @classmethod
    def get_device_object(cls):
        if cls._device is None:
            cls.connect()
        return cls._device


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
#         abi: str = ADB.get_device_object().shell('getprop ro.product.cpu.abi').strip()
#         sdk: int = int(ADB.get_device_object().shell('getprop ro.build.version.sdk').strip())
#         pre: str = ADB.get_device_object().shell('getprop ro.build.version.preview_sdk').strip()
#         rel: str = ADB.get_device_object().shell('getprop ro.build.version.release').strip()
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
#         ADB.get_device_object().shell(f'mkdir {dir} 2>/dev/null || true')
#
#         basepath = get_adb_path()
#         basepath = basepath[:basepath.rfind(os.path.sep)]  # remove adb.exe from basepath
#         basepath = os.path.join(basepath, "minicap")
#
#         # Push minicap binary
#         ADB.get_device_object().push(f'{basepath}/{abi}/bin/{bin}', f'{dir}/{bin}')
#         ADB.get_device_object().push(f'{basepath}/libs/android-{sdk}/{abi}/minicap.so', f'{dir}/minicap.so')
#
#         ADB.get_device_object().shell(f'chmod 777 {dir}/{bin} {dir}/{bin}.so')
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
