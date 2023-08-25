from arona.adb import ADB
import cv2
import numpy as np
from arona.resource import resource_path
import time

drawing = False
ix,iy = -1,-1

# Create a black image
img = np.zeros((1080,1920,3), np.uint8)

color_sample = False
color_max = [-1000, -1000, -1000]
color_min = [1000, 1000, 1000]

# define mouse callback function to draw rect
def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, img, screenshot, color_sample, color_max, color_min
    if event == cv2.EVENT_RBUTTONDOWN:
        color_max = [-1000, -1000, -1000]
        color_min = [1000, 1000, 1000]
        color_sample = True
        color = cv2.cvtColor(np.uint8([[img[y, x]]]), cv2.COLOR_BGR2HSV)[0][0]
        color_max = [max(int(color_max[i]), int(color[i])) for i in range(3)]
        color_min = [min(int(color_min[i]), int(color[i])) for i in range(3)]
        # take BGR pixel, print HSV
        # print(img[y, x][::-1], '=', cv2.cvtColor(np.uint8([[img[y, x]]]), cv2.COLOR_BGR2HSV)[0][0])
    if event == cv2.EVENT_MOUSEMOVE and color_sample:
        h, s, v = cv2.cvtColor(np.uint8([[img[y, x]]]), cv2.COLOR_BGR2HSV)[0][0]
        color_max = [max(color_max[0], h), max(color_max[1], s), max(color_max[2], v)]
        color_min = [min(color_min[0], h), min(color_min[1], s), min(color_min[2], v)]
    if event == cv2.EVENT_RBUTTONUP:
        color_sample = False
        print(color_max, color_min)
        color_avg = [(int(color_max[i]) + int(color_min[i])) // 2 for i in range(3)]
        tolerance = [3 + (abs(int(color_max[i]) - int(color_min[i])) // 2) for i in range(3)]
        color_avg = f"{color_avg[0]}-{color_avg[1]}-{color_avg[2]}"
        tolerance = f"{tolerance[0]}-{tolerance[1]}-{tolerance[2]}"
        print(f"mode: hsv\nhsv: {color_avg}\ntolerance: {tolerance}")
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
    screenshot = ADB.screencap_mat()
    img = screenshot.copy()
    # opencv show img and read two points from mouse click in the window
    cv2.namedWindow("Screen", cv2.WINDOW_AUTOSIZE)
    cv2.resizeWindow('Screen', img.shape[1], img.shape[0])
    cv2.setMouseCallback("Screen", draw_rectangle)
    while True:
        cv2.imshow("Screen", img)
        if cv2.waitKey(10) == 27:
            break
