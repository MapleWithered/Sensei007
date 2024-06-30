from arona import startup, momotalk, cafe, tasks, mail, battle, group, alchemy, schedule

if __name__ == '__main__':
    # # demoviewer.start_viewer()
    # startup.run_startup()
    #
    # # Tasks independent to rewards given
    # group.run_group()     # ok
    # battle.run_wanted()   # ok
    # battle.run_communication()    # ok
    # cafe.run_cafe()       # ok
    # # TODO: when list student already in cafe, run second priority or the last one
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

    # startup.stop_activity()
