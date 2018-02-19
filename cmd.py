#!/usr/bin/python3
import i3ipc
import json
import re
import subprocess
import sys

def rofi_args(prompt=">>"):
    return [
        'rofi', '-show', '-dmenu', '-columns', '14', '-lines', '2',  '-disable-history', '-p', prompt,
        '-case-sensitive=false', '-matching', 'fuzzy', '-theme-str', '* { font: "Iosevka Term Medium 14"; }',
        '-theme-str', '#window { width:1900; y-offset: -32; location: south; anchor: south; }',
    ]

def i3_cmds():
    try:
        lst=[t.replace("'",'') for t in re.split('\s*,\s*', json.loads(
                    subprocess.check_output(['i3-msg', 'sssssnake'], stderr=subprocess.DEVNULL)
                )[0]['error']
            )[2:]
        ]
        lst.remove('nop')
        lst.sort()
        return lst
    except:
        return ""

def i3_cmd_args(cmd):
    try:
        return [t.replace("'",'') for t in
            re.split('\s*,\s*',json.loads(
                    subprocess.check_output(['i3-msg', cmd], stderr=subprocess.DEVNULL)
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
        cmd = subprocess.check_output(rofi_args(),
            input=bytes('\n'.join(i3_cmds()), 'UTF-8')).decode('UTF-8').strip()
    except CalledProcessError as e:
        sys.exit(e.returncode)

    if not cmd:
        sys.exit(0) # nothing to do

    debug      = False
    ok         = False
    notify_msg = ""

    args=i3_cmd_args(cmd)
    prev_args=""
    while not (ok or args == ['<end>'] or args == []):
        if debug:
            print("evaluated cmd=[{}] args=[{}]".format(cmd,i3_cmd_args(cmd)))
        result = i3.command(cmd)
        ok = True
        if not result[0]['success']:
            ok = False
            notify_msg=['notify-send', 'i3-cmd error', result[0]['error']]
            try:
                args = i3_cmd_args(cmd)
                if args == prev_args:
                    break
                cmd += ' ' + subprocess.check_output(rofi_args(">> " + cmd),
                    input=bytes('\n'.join(args), 'UTF-8')).decode('UTF-8').strip()
                prev_args = args
            except CalledProcessError as e:
                sys.exit(e.returncode)

    if not ok:
        subprocess.Popen(notify_msg)

main()
