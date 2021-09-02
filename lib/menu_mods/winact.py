import subprocess
from functools import partial
from typing import Callable
from extension import extension


class winact():
    def __init__(self, menu):
        self.menu = menu

    def win_act_simple(self, cmd: str, prompt: str) -> None:
        """ Run simple and fast selection dialog for window with given action.
            Args:
                cmd (str): action for window to run.
                prompt (str): custom prompt for menu.
        """
        leaves = self.menu.i3ipc.get_tree().leaves()
        winlist = [win.name for win in leaves]
        winlist_len = len(winlist)
        menu_params = {
            'cnum': winlist_len,
            'prompt': f"{prompt} {self.menu.conf('prompt')}"
        }
        win_name = None
        if winlist and winlist_len > 1:
            win_name = subprocess.run(
                self.menu.args(menu_params),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(winlist), 'UTF-8'),
                check=False
            ).stdout
        elif winlist_len:
            win_name = winlist[0].encode()
        if win_name is not None and win_name:
            win_name = win_name.decode('UTF-8').strip()
            for win in leaves:
                if win.name == win_name:
                    win.command(cmd)

    def goto_win(self) -> None:
        """ Run menu goto selection dialog """
        self.win_act_simple('focus', self.menu.wrap_str('go'))

    def attach_win(self) -> None:
        """ Attach window to the current workspace. """
        self.win_act_simple(
            'move window to workspace current', self.menu.wrap_str('attach')
        )

    def select_ws(self) -> str:
        """ Apply target function to workspace. """
        ws_list = extension.get_mods()['conf_gen'].cfg['workspaces']
        menu_params = {
            'cnum': len(ws_list),
            'prompt': f'{self.menu.wrap_str("ws")} {self.menu.conf("prompt")}',
        }
        try:
            workspace_name = subprocess.run(
                self.menu.args(menu_params),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(ws_list), 'UTF-8'),
                check=False
            ).stdout
            selected_ws = workspace_name.decode('UTF-8').strip()
            if selected_ws:
                num = ws_list.index(selected_ws) + 1
                return str(f'{num} :: {selected_ws}')
        except Exception:
            return ''
        return ''

    @staticmethod
    def apply_to_ws(ws_func: Callable) -> None:
        """ Partial apply function to workspace. """
        ws_func()

    def goto_ws(self) -> None:
        """ Go to workspace menu. """
        workspace_name = self.select_ws()
        if workspace_name is not None and workspace_name:
            ws_splitname = workspace_name.split('::')
            if len(ws_splitname) > 1:
                ws_num = ws_splitname[0].strip()
                self.apply_to_ws(
                    partial(
                        self.menu.i3ipc.command, f'workspace number {ws_num}'
                    )
                )

    def move_to_ws(self) -> None:
        """ Move current window to the selected workspace """
        workspace_name = self.select_ws()
        if workspace_name is not None and workspace_name:
            ws_splitname = workspace_name.split('::')
            if len(ws_splitname) > 1:
                ws_num = ws_splitname[0].strip()
                self.apply_to_ws(
                    partial(self.menu.i3ipc.command,
                            f'[con_id=__focused__] \
                            move to workspace number {ws_num}')
                )
