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
hsv_max = [-1000, -1000, -1000]
hsv_min = [1000, 1000, 1000]
rgb_max = [-1000, -1000, -1000]
rgb_min = [1000, 1000, 1000]

# define mouse callback function to draw rect
def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, img, screenshot, color_sample, hsv_max, hsv_min, rgb_max, rgb_min
    if event == cv2.EVENT_RBUTTONDOWN:
        hsv_max = [-1000, -1000, -1000]
        hsv_min = [1000, 1000, 1000]
        rgb_max = [-1000, -1000, -1000]
        rgb_min = [1000, 1000, 1000]
        color_sample = True
        rgb_max = [max(rgb_max[i], int(img[y, x][::-1][i])) for i in range(3)]
        rgb_min = [min(rgb_min[i], int(img[y, x][::-1][i])) for i in range(3)]
        color = cv2.cvtColor(np.uint8([[img[y, x]]]), cv2.COLOR_BGR2HSV)[0][0]
        hsv_max = [max(int(hsv_max[i]), int(color[i])) for i in range(3)]
        hsv_min = [min(int(hsv_min[i]), int(color[i])) for i in range(3)]
        # take BGR pixel, print HSV
        # print(img[y, x][::-1], '=', cv2.cvtColor(np.uint8([[img[y, x]]]), cv2.COLOR_BGR2HSV)[0][0])
    if event == cv2.EVENT_MOUSEMOVE and color_sample:
        rgb = img[y, x][::-1]
        rgb_max = [max(rgb_max[i], int(rgb[i])) for i in range(3)]
        rgb_min = [min(rgb_min[i], int(rgb[i])) for i in range(3)]
        h, s, v = cv2.cvtColor(np.uint8([[img[y, x]]]), cv2.COLOR_BGR2HSV)[0][0]
        hsv_max = [max(hsv_max[0], h), max(hsv_max[1], s), max(hsv_max[2], v)]
        hsv_min = [min(hsv_min[0], h), min(hsv_min[1], s), min(hsv_min[2], v)]
    if event == cv2.EVENT_RBUTTONUP:
        color_sample = False
        rgb_medium = [(int(rgb_max[i]) + int(rgb_min[i])) // 2 for i in range(3)]
        rgb_tolerance = [3 + (abs(int(rgb_max[i]) - int(rgb_min[i])) // 2) for i in range(3)]
        rgb_medium = f"{rgb_medium[0]}-{rgb_medium[1]}-{rgb_medium[2]}"
        rgb_tolerance = f"{rgb_tolerance[0]}-{rgb_tolerance[1]}-{rgb_tolerance[2]}"
        hsv_medium = [(int(hsv_max[i]) + int(hsv_min[i])) // 2 for i in range(3)]
        hsv_tolerance = [3 + (abs(int(hsv_max[i]) - int(hsv_min[i])) // 2) for i in range(3)]
        hsv_medium = f"{hsv_medium[0]}-{hsv_medium[1]}-{hsv_medium[2]}"
        hsv_tolerance = f"{hsv_tolerance[0]}-{hsv_tolerance[1]}-{hsv_tolerance[2]}"
        pos = f"{x}-{y}"
        print(f"pos_end: {x}-{y}\nrgb_medium: {rgb_medium}\nrgb_tolerance: {rgb_tolerance}\nhsv_medium: {hsv_medium}\nhsv_tolerance: {hsv_tolerance}")
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
