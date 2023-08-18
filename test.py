from arona import startup, momotalk
from arona.adb import ADB
from arona.cafe import run_cafe
from arona.imgreco import match_res
from arona.presser import wait_n_press_res

if __name__ == '__main__':
    print(match_res("navigation.btn_main_menu"))