#!/usr/bin/python3
import json
import re
import subprocess
import sys

from singleton_mixin import *

class i3menu(SingletonMixin):
    def rofi_args(self, prompt=">>"):
        return [
            'rofi', '-show', '-dmenu',
            '-columns', '16', '-lines', '2',
            '-disable-history',
            '-p', prompt,
            '-case-sensitive=false',
            '-matching', 'fuzzy',
            '-theme-str', '* { font: "Iosevka Term Medium 14"; }',
            '-theme-str', '#window { width:1900; y-offset: -32; location: south; anchor: south; }',
        ]

    def i3_cmds(self):
        try:
            p=subprocess.Popen(
                ['i3-msg', 'sssssnake'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )

            lst=[t.replace("'",'') for t in re.split('\s*,\s*', json.loads(
                p.communicate()[0]
            )[0]['error'])[2:]]

            p.wait()

            lst.remove('nop')
            lst.append('splitv')
            lst.append('splith')
            lst.sort()
            return lst
        except:
            return ""

    def i3_cmd_args(self, cmd):
        try:
            p=subprocess.Popen(
                ['i3-msg', cmd],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )
            ret=[t.replace("'",'') for t in
                re.split('\s*,\s*',json.loads(
                        p.communicate()[0]
                    )[0]['error']
                )[1:]
            ]
            p.wait()
            return ret
        except:
            return None

    def main(self):
        # set default menu args for supported menus
        cmd = ''

        try:
            p=subprocess.Popen(
                self.rofi_args(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
            p.stdin.write(bytes('\n'.join(self.i3_cmds()), 'UTF-8'))
            p_com=p.communicate()[0]
            p.wait()
            if p_com is not None:
                cmd = p_com.decode('UTF-8').strip()
            p.stdin.close()
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

        if not cmd:
            sys.exit(0) # nothing to do

        debug      = False
        ok         = False
        notify_msg = ""

        args=None
        prev_args=None
        while not (ok or args == ['<end>'] or args == []):
            if debug:
                print("evaluated cmd=[{}] args=[{}]".format(cmd, self.i3_cmd_args(cmd)))
            p=subprocess.Popen( ("i3-msg " +  cmd).split(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            r = json.loads(p.communicate()[0].decode('UTF-8').strip())
            result = r[0]['success']
            p.wait()
            ok = True
            if not result:
                ok = False
                notify_msg=['notify-send', 'i3-cmd error', r[0]['error']]
                try:
                    args = self.i3_cmd_args(cmd)
                    if args == prev_args:
                        sys.exit(0)
                    p=subprocess.Popen(
                        self.rofi_args(">> " + cmd),
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE
                    )
                    p.stdin.write(bytes('\n'.join(args), 'UTF-8'))
                    cmd += ' ' + p.communicate()[0].decode('UTF-8').strip()
                    prev_args = args
                    p.stdin.close()
                    p.wait()
                except subprocess.CalledProcessError as e:
                    sys.exit(e.returncode)

        if not ok:
            subprocess.Popen(notify_msg)

if __name__ == '__main__':
    menu = i3menu().instance()
    menu.main()
