from arona import startup, momotalk, cafe, presser, tasks, mail, battle, group, alchemy, schedule
from arona.adb import ADB, MNT
from arona.cafe import run_cafe
from arona.imgreco import *
from arona.presser import wait_n_press_res
from arona import resource as res
from arona.demoviewer import demoviewer

import time
import socket

if __name__ == '__main__':
    # demoviewer.start_viewer()
    startup.run_startup()

    # Tasks independent to rewards given
    group.run_group()     # ok
    battle.run_wanted()   # ok
    battle.run_communication()    # ok
    cafe.run_cafe()       # ok
    schedule.run_schedule()   # ok
    momotalk.run_momotalk()   # ok
    mail.run_mail()                   # ok
    tasks.run_tasks()                 # ok

    battle.run_competition()  # ok

    # TODO: not implemented
    # tasks.recover_ap()
    # battle.run_task() total 20
    # shop.buy_daily()

    alchemy.run_alchemy()     # ok
    tasks.run_tasks()       # ok

    ADB._cap_daemon_run = False
