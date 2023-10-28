#!/usr/bin/env python
import subprocess
import logging
import i3ipc
import i3ipc.con
from typing import List

class menu():
    @staticmethod
    def args(P: dict, prompt='❯>') -> List[str]:
        """ Create run parameters to spawn menu process from dict
            P(dict): parameters for menu
            List(str) to do menu subprocessing """
        return [
            'rofi', 
            '-show',
            '-dmenu',
            '-disable-history',
            '-auto-select',
            '-markup-rows',
            '-p', P.get('prompt', prompt),
            '-i',
            '-matching', 'glob'
        ]

    @staticmethod
    def wrap_str(s: str, lfs='⟬', rhs='⟭') -> str:
        """ String wrapper to make it beautiful """
        return f'{lfs}{s}{rhs}'

@staticmethod
def print_run_exception_info(proc_err):
    logging.info(f'returncode={proc_err.returncode}, \
                    cmd={proc_err.cmd}, \
                    output={proc_err.output}')

class xprop():
    """ Setup screen resolution """
    def __init__(self):
        self.xprops_list=[
            'WM_CLASS', 'WM_NAME', 'WM_WINDOW_ROLE', 'WM_TRANSIENT_FOR',
            '_NET_WM_WINDOW_TYPE', '_NET_WM_STATE', '_NET_WM_PID'
        ]
        self.prompt='❯>'
        self.i3ipc=i3ipc.Connection()

    def xprop(self) -> None:
        """ Menu to show X11 atom attributes for current window. """
        xprops = []
        target_win = self.i3ipc.get_tree().find_focused()
        try:
            xprop_ret = subprocess.run(
                ['xprop', '-id', str(target_win.window)] +
                self.xprops_list,
                stdout=subprocess.PIPE,
                check=True
            ).stdout
            if xprop_ret is not None:
                xprop_ret = xprop_ret.decode().split('\n')
                for line in xprop_ret:
                    if 'not found' not in line:
                        xprops.append(line)
        except subprocess.CalledProcessError as proc_err:
            print_run_exception_info(proc_err)
        menu_params = {'prompt': f'{menu.wrap_str("xprop")} {self.prompt}'}
        ret = ""
        try:
            xprop_sel = subprocess.run(
                menu.args(menu_params),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(xprops), 'UTF-8'),
                check=True
            ).stdout

            if xprop_sel is not None:
                ret = xprop_sel.decode('UTF-8').strip()
        except subprocess.CalledProcessError as proc_err:
            print_run_exception_info(proc_err)
        if ret is not None and ret != '':
            try:
                # Copy to the clipboard
                subprocess.run(['xsel', '-i'], input=bytes(ret.strip(), 'UTF-8'), check=True)
            except subprocess.CalledProcessError as proc_err:
                print_run_exception_info(proc_err)

def main():
    xprop().xprop()

if __name__ == '__main__':
    main()
