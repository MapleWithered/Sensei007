from arona import startup, momotalk, cafe, tasks, mail, battle, group, alchemy, schedule

if __name__ == '__main__':
    # demoviewer.start_viewer()
    startup.run_startup()
    tasks.run_tasks()

    # Tasks independent to rewards given
    group.run_group()
    battle.run_wanted()
    battle.run_communication()
    cafe.run_cafe()
    # TODO: when list student already in cafe, run second priority or the last one
    schedule.run_schedule()
    momotalk.run_momotalk()
    mail.run_mail()
    tasks.run_tasks()

    battle.run_competition()

    # TODO: not implemented
    # tasks.recover_ap()
    # battle.run_task() total 20
    # shop.buy_daily()

    alchemy.run_alchemy()
    tasks.run_tasks()

    # startup.stop_activity()
