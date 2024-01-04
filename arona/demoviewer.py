import time

import cv2
import numpy as np

import threading

from .adb import ADB


class demoviewer:
    mat = None
    lock = threading.Lock()

    rect_toshow = []

    use_viewer = False

    @classmethod
    def start_viewer(cls):
        # cls.mat = ADB.screencap_mat()
        cls.use_viewer = True

        # Start new thread to continuously imshow mat updated by other threads
        def imshow_thread():
            width = 1920
            height = 1080
            while cls.use_viewer:
                if ADB.get_loading_countdown() == 3:
                    demoviewer.show_img([[1381, 962, 1684, 1023]])
                mat = np.zeros((height, width, 3), np.uint8)
                # greenboard
                mat[:, :, 1] = 255
                next_rect = 0
                for i in range(len(cls.rect_toshow)):
                    if time.time() - cls.rect_toshow[i][1] < 1.5:
                        next_rect = i
                        break
                cls.rect_toshow = cls.rect_toshow[next_rect:]
                for rect, _ in cls.rect_toshow:
                    cv2.rectangle(mat, (int(rect[0]), int(rect[1])), (int(rect[2]), int(rect[3])), (0, 0, 255), 5)
                cv2.imshow("Demo viewer", mat)
                cv2.waitKey(30)

        threading.Thread(target=imshow_thread, daemon=True).start()

    @classmethod
    def stop_viewer(cls):
        cls.use_viewer = False
        time.sleep(0.1)
        cv2.destroyAllWindows()

    @classmethod
    def show_img(cls, rects: list[list]):
        if not cls.use_viewer:
            return
        for rect in rects:
            cls.rect_toshow.append((rect, time.time()))
