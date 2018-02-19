#!/usr/bin/python3
import i3ipc
import json
import re
import subprocess
from sys import exit
from os.path import basename

prompt=">>"
rofi_args = [
    'rofi', '-show', '-dmenu', '-columns', '10', '-lines', '2',  '-p', prompt
]

def get_cmds():
    try:
        return [t.replace("'",'') for t in re.split('\s*,\s*',json.loads(
                    subprocess.check_output(['i3-msg', 'sssssnake'], stderr=subprocess.DEVNULL)
                )[0]['error']
            )[2:]
        ]
    except:
        return ""

def get_args(cmd):
    try:
        return [t.replace("'",'') for t in
            re.split('\s*,\s*',json.loads(
                    subprocess.check_output(['i3-msg', cmd, 'ssssnake'], stderr=subprocess.DEVNULL)
                )[0]['error']
            )[1:]
        ]
    except:
        return ""

def main():
    i3 = i3ipc.Connection()
    # set default menu args for supported menus
    cmd = ''

    try:
        cmd = subprocess.check_output(rofi_args,
            input=bytes('\n'.join(get_cmds()), 'UTF-8')).decode('UTF-8').strip()
    except CalledProcessError as e:
        exit(e.returncode)

    if not cmd:
        exit(0) # nothing to do

    cmd_success = False
    notify_msg=""

    while not (cmd_success or get_args(cmd) == ['<end>'] or get_args(cmd) == []):
        print("evaluated cmd=[{}]".format(cmd))
        result = i3.command(cmd)
        cmd_success = True
        if not result[0]['success']:
            cmd_success = False
            notify_msg=['notify-send', 'i3-cmd error', result[0]['error']]
            try:
                cmd += ' ' + subprocess.check_output(rofi_args,
                    input=bytes('\n'.join(get_args(cmd)), 'UTF-8')).decode('UTF-8').strip()
            except CalledProcessError as e:
                exit(e.returncode)

    if not cmd_success:
        subprocess.Popen(notify_msg)

main()
