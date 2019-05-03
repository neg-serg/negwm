import sys
import json
import re
import subprocess

from typing import List


class i3menu():
    def __init__(self, menu):
        self.menu = menu

    def i3_cmds(self) -> List[str]:
        """ Return the list of i3 commands with magic_pie hack autocompletion.
        """
        try:
            out = subprocess.run(
                [self.menu.i3cmd, 'magic_pie'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            ).stdout
        except Exception:
            return []

        lst = [
            t.replace("'", '')
            for t in re.split('\\s*,\\s*', json.loads(
                out.decode('UTF-8')
            )[0]['error'])[2:]
        ]

        lst.remove('nop')
        lst.extend(['splitv', 'splith'])
        lst.sort()

        return lst

    def i3_cmd_args(self, cmd: str) -> List[str]:
        try:
            out = subprocess.run(
                [self.menu.i3cmd, cmd],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            ).stdout
            if out is not None:
                ret = [
                    t.replace("'", '') for t in
                    re.split('\\s*, \\s*', json.loads(
                                out.decode('UTF-8')
                            )[0]['error'])[1:]
                ]
            return ret
        except Exception:
            return None

    def cmd_menu(self) -> int:
        """ Menu for i3 commands with hackish autocompletion.
        """
        # set default menu args for supported menus
        cmd = ''

        try:
            cmd_rofi = subprocess.run(
                self.menu.rofi_args(),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(self.i3_cmds()), 'UTF-8')
            ).stdout
            if cmd_rofi is not None and cmd_rofi:
                cmd = cmd_rofi.decode('UTF-8').strip()
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)

        if not cmd:
            # nothing to do
            return 0

        debug, ok, notify_msg = False, False, ""
        args, prev_args = None, None
        while not (ok or args == ['<end>'] or args == []):
            if debug:
                print(f"evaluated cmd=[{cmd}] args=[{self.i3_cmd_args(cmd)}]")
            out = subprocess.run(
                (f"{self.menu.i3cmd} " + cmd).split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout
            if out is not None and out:
                r = json.loads(out.decode('UTF-8').strip())
                result = r[0].get('success', '')
                err = r[0].get('error', '')
                ok = True
                if not result:
                    ok = False
                    notify_msg = ['notify-send', 'i3-cmd error', err]
                    try:
                        args = self.i3_cmd_args(cmd)
                        if args == prev_args:
                            return 0
                        cmd_rerun = subprocess.run(
                            self.rofi_args(
                                f"{self.menu.wrap_str('i3cmd')}" +
                                " {self.menu.prompt} " + cmd
                            ),
                            stdout=subprocess.PIPE,
                            input=bytes('\n'.join(args), 'UTF-8')
                        ).stdout
                        cmd += ' ' + cmd_rerun.decode('UTF-8').strip()
                        prev_args = args
                    except subprocess.CalledProcessError as e:
                        return e.returncode

        if not ok:
            subprocess.run(notify_msg)

