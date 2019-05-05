import subprocess


class xprop():
    def __init__(self, menu):
        self.menu = menu

    def xprop_menu(self) -> None:
        """ Menu to show X11 atom attributes for current window.
        """
        xprops = []
        w = self.menu.i3.get_tree().find_focused()
        xprop = subprocess.run(
            ['xprop', '-id', str(w.window)] + self.menu.xprops_list,
            stdout=subprocess.PIPE
        ).stdout
        if xprop is not None:
            xprop = xprop.decode().split('\n')
            for line in xprop:
                if 'not found' not in line:
                    xprops.append(line)

        rofi_params = {
            'cnum': 1,
            'lnum': len(xprops),
            'width': int(self.menu.screen_width * 0.75),
            'prompt': f'{self.menu.wrap_str("xprop")} {self.menu.prompt}'
        }
        xprop_sel = subprocess.run(
            self.menu.rofi_args(rofi_params),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(xprops), 'UTF-8')
        ).stdout

        if xprop_sel is not None:
            ret = xprop_sel.decode('UTF-8').strip()

        # Copy to the clipboard
        if ret is not None and ret != '':
            subprocess.run(['xsel', '-i'], input=bytes(ret.strip(), 'UTF-8'))

