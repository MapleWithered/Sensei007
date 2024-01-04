import keyboard
import time

if __name__ == '__main__':

    event_list = []
    def callback(event):
        event_list.append((event.time, event.name))


    keyboard.hook(callback=callback)
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
    for i in event_list:
        print(i[0], i[1])

