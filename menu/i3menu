#!/usr/bin/env python
import json
import logging
import re
import subprocess
import sys

from typing import List


class i3menu():
    def __init__(self):
        self.i3cmd = 'i3-msg'
        self.left_bracket='⟬'
        self.prompt='❯>'
        self.right_bracket='⟭'

    def args(self, params: dict) -> List[str]:
        """ Create run parameters to spawn rofi process from dict
            params(dict): parameters for rofi
            List(str) to do rofi subprocessing """
        matching='fuzzy'

        params['prompt'] = self.prompt
        params['markup_rows'] = params.get('markup_rows', '-no-markup-rows')
        params['auto-select'] = \
            params.get('auto-select', "-no-auto-select")
        return [
            'rofi', '-show', '-dmenu', '-disable-history',
            params['auto-select'], params['markup_rows'],
            '-p', params['prompt'], '-i', '-matching', f'{matching}']

    def wrap_str(self, string: str) -> str:
        """ String wrapper to make it beautiful """
        return self.left_bracket + string + self.right_bracket

    def i3_cmds(self) -> List[str]:
        """ Return the list of i3 commands with magic_pie hack autocompletion. """
        try:
            out = subprocess.run(
                [self.i3cmd, 'magic_pie'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False
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
        ret = ['']
        try:
            out = subprocess.run(
                [self.i3cmd, cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False
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
            return ['']

    def i3menu(self) -> int:
        """ Menu for i3 commands with hackish autocompletion. """
        # set default menu args for supported menus
        cmd = ''
        try:
            menu = subprocess.run(
                self.args({}),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(self.i3_cmds()), 'UTF-8'),
                check=True
            ).stdout
            if menu is not None and menu:
                cmd = menu.decode('UTF-8').strip()
        except subprocess.CalledProcessError as call_e:
            sys.exit(call_e.returncode)

        if not cmd:
            # nothing to do
            return 0

        debug, ok, notify_msg = False, False, ""
        args, prev_args = None, None
        menu_params = {
            'prompt': f"{self.wrap_str('i3cmd')} \
                {self.prompt} " + cmd,
        }
        while not (ok or args == ['<end>'] or args == []):
            if debug:
                logging.debug(f"evaluated cmd=[{cmd}] args=[{self.i3_cmd_args(cmd)}]")
            out = subprocess.run(
                (f"{self.i3cmd} " + cmd).split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            ).stdout
            if out is not None and out:
                ret = json.loads(out.decode('UTF-8').strip())[0]
                result, err = ret.get('success', ''), ret.get('error', '')
                ok = True
                if not result:
                    ok = False
                    notify_msg = ['notify-send', 'i3-cmd error', err]
                    try:
                        args = self.i3_cmd_args(cmd)
                        if args == prev_args:
                            return 0
                        cmd_rerun = subprocess.run(
                            self.args(menu_params),
                            stdout=subprocess.PIPE,
                            input=bytes('\n'.join(args), 'UTF-8'),
                            check=False
                        ).stdout
                        cmd += ' ' + cmd_rerun.decode('UTF-8').strip()
                        prev_args = args
                    except subprocess.CalledProcessError as call_e:
                        return call_e.returncode

        if not ok:
            subprocess.run(notify_msg, check=False)

        return 0

if __name__ == '__main__':
    i3menu().i3menu()
