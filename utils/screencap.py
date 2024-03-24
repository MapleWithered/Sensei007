import cv2

from arona.adb import ADB

if __name__ == '__main__':
    counter = 0
    while True:
        counter += 1
        mat = ADB.screencap_mat(force=True)
        cv2.imshow("Screen", mat)
        if cv2.waitKey(10) == 27:
            break
        print(counter)
