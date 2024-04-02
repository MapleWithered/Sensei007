from . import scrcpy, adb_legacy
from .. import config

# when import this adb.py, read config file to decide whether scrcpy.ADB or adb_legacy.ADB should be used

if config.get_config("arona.yaml/device.screencap") == "adb":
    ADB = adb_legacy.ADB
    MNT = adb_legacy.MNT
else:
    ADB = scrcpy.ADB
    MNT = scrcpy.MNT
