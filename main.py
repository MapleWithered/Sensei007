from arona import startup, momotalk, cafe, presser, tasks, mail, battle, group, alchemy
from arona.adb import ADB, MNT
from arona.cafe import run_cafe
from arona.imgreco import *
from arona.presser import wait_n_press_res
from arona import resource as res

import time
import socket

if __name__ == '__main__':
    startup.run_startup()

    battle.run_wanted()
    group.run_group()
    mail.run_mail()
    cafe.run_cafe(force=True)
    momotalk.run_momotalk()
    alchemy.run_alchemy()
    tasks.run_tasks()
    battle.run_wanted()

    tasks.run_tasks()
    ADB._cap_daemon_run = False
