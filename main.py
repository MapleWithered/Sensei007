from arona import startup, momotalk, cafe, presser, tasks, mail
from arona.adb import ADB, MNT
from arona.cafe import run_cafe
from arona.imgreco import match_res
from arona.presser import wait_n_press_res

import time
import socket

if __name__ == '__main__':
    startup.run_startup()
    mail.run_mail()
    cafe.run_cafe()
    momotalk.run_momotalk()
    tasks.run_tasks()
    ADB._cap_daemon_run = False
    # # MNC.init_device()
    # ADB.get_device_object().forward("tcp:16380", "tcp:16380")
    # counter = 0
    # start_time = time.time()
    # while True:
    #     conn = ADB.get_device_object().create_connection(timeout=None)
    #     cmd = "shell:{}".format("screencap -p | nc -p 16380 -l >/dev/null")
    #     conn.send(cmd)
    #     # get response from socks: localhost:16380
    #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     img_raw = b''
    #     try:
    #         sock.connect(("127.0.0.1", 16380))
    #         while True:
    #             data = sock.recv(1024)
    #             if not data:
    #                 break
    #             img_raw += data
    #     except Exception as e:
    #         print(e)
    #     finally:
    #         sock.close()
    #     counter += 1 if len(img_raw) > 0 else 0
    #     print(counter, len(img_raw), 1/(time.time()-start_time)*counter)
    #     conn.close()