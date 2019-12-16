import subprocess


class xrandr():
    def __init__(self, menu):
        self.menu = menu

    def change_resolution_xrandr(self):
        from display import Display
        xrandr_data = Display.xrandr_resolution_list()
        menu_params = {
            'cnum': 8,
            'width': int(Display.get_screen_resolution()["width"] * 0.55),
            'prompt': f'{self.menu.wrap_str("gtk_theme")} \
            {self.menu.conf("prompt")}',
        }
        resolution_sel = subprocess.run(
            self.menu.args(menu_params),
            stdout=subprocess.PIPE,
            input=bytes('\n'.join(xrandr_data), 'UTF-8'),
            check=False
        ).stdout

        if resolution_sel is not None:
            ret = resolution_sel.decode('UTF-8').strip()

        ret_list = []
        if ret and 'x' in ret:
            size_pair = ret.split(':')
            size_id = size_pair[0]
            res_str = size_pair[1:][0].strip()
            ret_list = res_str.split('x')

        width, height = ret_list[0].strip(), ret_list[1].strip()

        print(f'Set size to {width}x{height}')
        Display.set_screen_size(size_id)
