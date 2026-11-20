# -*- coding: utf-8 -*-
"""VLC Remote Controller Engine - Command Dispatcher"""
def build_vlc_rc_command(action, volume_delta=0):
    cmd_map = {
        "play": "play\n",
        "pause": "pause\n",
        "next": "next\n",
        "prev": "prev\n",
        "volup": f"volup {volume_delta}\n",
        "voldown": f"voldown {volume_delta}\n"
    }
    return cmd_map.get(action, "status\n")
