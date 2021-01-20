import subprocess
from misc import Misc


class xprop():
    """ Setup screen resolution """
    def __init__(self, menu):
        self.menu = menu

    def xprop(self) -> None:
        """ Menu to show X11 atom attributes for current window. """
        xprops = []
        target_win = self.menu.i3ipc.get_tree().find_focused()
        try:
            xprop_ret = subprocess.run(
                ['xprop', '-id', str(target_win.window)] +
                self.menu.xprops_list,
                stdout=subprocess.PIPE,
                check=True
            ).stdout
            if xprop_ret is not None:
                xprop_ret = xprop_ret.decode().split('\n')
                for line in xprop_ret:
                    if 'not found' not in line:
                        xprops.append(line)
        except subprocess.CalledProcessError as proc_err:
            Misc.print_run_exception_info(proc_err)
        menu_params = {
            'cnum': 1,
            'lnum': len(xprops),
            'width': int(self.menu.screen_width * 0.75),
            'prompt':
                f'{self.menu.wrap_str("xprop")} {self.menu.conf("prompt")}'
        }
        ret = ""
        try:
            xprop_sel = subprocess.run(
                self.menu.args(menu_params),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(xprops), 'UTF-8'),
                check=True
            ).stdout

            if xprop_sel is not None:
                ret = xprop_sel.decode('UTF-8').strip()
        except subprocess.CalledProcessError as proc_err:
            Misc.print_run_exception_info(proc_err)
        if ret is not None and ret != '':
            try:
                # Copy to the clipboard
                subprocess.run(['xsel', '-i'], input=bytes(ret.strip(), 'UTF-8'), check=True)
            except subprocess.CalledProcessError as proc_err:
                Misc.print_run_exception_info(proc_err)
