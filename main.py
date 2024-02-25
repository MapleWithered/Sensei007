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
    group.run_group()
    battle.run_wanted()
    cafe.run_cafe()
    schedule.run_schedule()
    momotalk.run_momotalk()
    mail.run_mail()
    tasks.run_tasks()


    battle.run_competition()

    # tasks.recover_ap()
    # battle.run_task() total 20
    # shop.buy_daily()

    alchemy.run_alchemy(boost=False)
    tasks.run_tasks()

    ADB._cap_daemon_run = False
    startup.stop_activity()
