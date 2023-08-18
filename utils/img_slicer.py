from arona.adb import ADB
import cv2
import numpy as np
from arona.resource import resource_path
import time

drawing = False
ix,iy = -1,-1

# Create a black image
img = np.zeros((1080,1920,3), np.uint8)

# define mouse callback function to draw rect
def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, img, screenshot
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix = x
        iy = y
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        cv2.rectangle(img, (ix, iy), (x, y), (0, 0, 255), 1)
        iy, y = sorted([iy, y])
        ix, x = sorted([ix, x])
        # slice rect out from screenshot
        sliced = screenshot[iy:y, ix:x]
        cv2.imshow("Sliced", sliced)
        # save to resource
        timestamp = int(time.time())
        cv2.imwrite(f"{resource_path}/1.78/{ix}-{iy}-{x}-{y}-{timestamp}.png", sliced)
        print(f"{ix}-{iy}-{x}-{y}-{timestamp}.png")


if __name__ == '__main__':
    screenshot = ADB.screencap_mat(force=True, std_size=True, gray=False)
    img = screenshot.copy()
    # opencv show img and read two points from mouse click in the window
    cv2.namedWindow("Screen", cv2.WINDOW_AUTOSIZE)
    cv2.resizeWindow('Screen', img.shape[1], img.shape[0])
    cv2.setMouseCallback("Screen", draw_rectangle)
    while True:
        cv2.imshow("Screen", img)
        if cv2.waitKey(10) == 27:
            break
