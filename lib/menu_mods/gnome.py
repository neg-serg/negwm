""" Change gtk / icons themes and another gnome settings """
import os
import configparser
import subprocess
import pathlib

from misc import Misc


class gnome():
    """ Change gtk / icons themes and another gnome settings using
    gsd-xsettings. """
    def __init__(self, menu):
        self.menu = menu
        self.gtk_config = configparser.ConfigParser()
        self.gsettings_script = os.path.expanduser(
            Misc.i3path() + 'bin/gnome-conf'
        )

    def menu_params(self, length, prompt):
        """ Set menu params """
        return {
            'cnum': length / 2,
            'lnum': 2,
            'prompt':
                f'{self.menu.wrap_str(prompt)} {self.menu.conf("prompt")}'
        }

    def apply_settings(self):
        """ Apply selected gnome settings """
        try:
            subprocess.Popen([self.gsettings_script])
        except subprocess.CalledProcessError as proc_err:
            Misc.print_run_exception_info(proc_err)

    def change_icon_theme(self):
        """ Changes icon theme with help of gsd-xsettings """
        icon_dirs = []
        icons_path = pathlib.Path('~/.local/share/icons').expanduser()
        for icon in icons_path.glob('*'):
            if icon:
                icon_dirs += [pathlib.Path(icon).name]
        menu_params = self.menu_params(len(icon_dirs), 'icon theme')
        selection = ''
        if not icon_dirs:
            return
        if len(icon_dirs) == 1:
            selection = icon_dirs[0]
        else:
            try:
                selection = subprocess.run(
                    self.menu.args(menu_params),
                    stdout=subprocess.PIPE,
                    input=bytes('\n'.join(icon_dirs), 'UTF-8'),
                    check=True
                ).stdout
            except subprocess.CalledProcessError as proc_err:
                Misc.print_run_exception_info(proc_err)
        if selection:
            os.environ.update({'GUI_ICONS': selection.decode('UTF-8').strip()})
            self.apply_settings()

    def change_gtk_theme(self):
        """ Changes gtk theme with help of gsd-xsettings """
        theme_dirs = []
        gtk_theme_path = pathlib.Path('~/.local/share/themes').expanduser()
        for theme in gtk_theme_path.glob('*/*/gtk.css'):
            if theme:
                theme_dirs += [pathlib.PurePath(theme).parent.parent.name]
        menu_params = self.menu_params(len(theme_dirs), 'gtk theme')
        selection = ''
        if not theme_dirs:
            return

        if len(theme_dirs) == 1:
            selection = theme_dirs[0]
        else:
            try:
                selection = subprocess.run(
                    self.menu.args(menu_params),
                    stdout=subprocess.PIPE,
                    input=bytes('\n'.join(theme_dirs), 'UTF-8'),
                    check=True
                ).stdout
            except subprocess.CalledProcessError as proc_err:
                Misc.print_run_exception_info(proc_err)
        if selection:
            os.environ.update({'GUI_GTK_THEME': selection.decode('UTF-8').strip()})
            self.apply_settings()
