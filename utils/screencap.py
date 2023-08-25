from arona import startup, momotalk, cafe, presser
from arona.adb import ADB, MNT
from arona.cafe import run_cafe
from arona.imgreco import match_res
from arona.presser import wait_n_press_res

import cv2

if __name__ == '__main__':
    counter = 0
    while True:
        counter += 1
        mat = ADB.screencap_mat(force=True)
        cv2.imshow("Screen", mat)
        if cv2.waitKey(10) == 27:
            break
        print(counter)
