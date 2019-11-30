""" Change gtk / icons themes and another gnome settings
"""
import os
import configparser
import subprocess
import glob
import path

from misc import Misc


class gnome():
    """
    Change gtk / icons themes and another gnome settings using
    gsd-xsettings.
    """

    def __init__(self, menu):
        self.menu = menu
        self.gtk_config = configparser.ConfigParser()
        self.gnome_settings_script = os.path.expanduser(
            '~/bin/scripts/gnome_settings'
        )

    def rofi_params(self, length, prompt):
        """ Set rofi params """
        return {
            'cnum': length / 2,
            'lnum': 2,
            'width': int(self.menu.screen_width * 0.55),
            'prompt':
                f'{self.menu.wrap_str(prompt)} {self.menu.conf("prompt")}'
        }

    def apply_settings(self, selection, *cmd_opts):
        """ Apply selected gnome settings """
        ret = ""
        if selection is not None:
            ret = selection.decode('UTF-8').strip()

            if ret is not None and ret != '':
                try:
                    subprocess.call([
                        self.gnome_settings_script, *cmd_opts, ret
                    ], check=True)
                except CalledProcessError as proc_err:
                    Misc.print_run_exception_info(proc_err)

    def change_icon_theme(self):
        """ Changes icon theme with help of gsd-xsettings """
        icon_dirs = []
        icons_path = path.Path('~/.icons').expanduser()
        for icon in glob.glob(icons_path + '/*'):
            if icon:
                icon_dirs += [path.Path(icon).name]

        rofi_params = self.rofi_params(len(icon_dirs), 'icon theme')

        try:
            selection = subprocess.run(
                self.menu.rofi_args(rofi_params),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(icon_dirs), 'UTF-8'),
                check=True
            ).stdout
        except CalledProcessError as proc_err:
            Misc.print_run_exception_info(proc_err)

        self.apply_settings(selection, '-i')

    def change_gtk_theme(self):
        """ Changes gtk theme with help of gsd-xsettings """
        theme_dirs = []
        gtk_theme_path = path.Path('~/.themes').expanduser()
        for theme in glob.glob(gtk_theme_path + '/*/*/gtk.css'):
            if theme:
                theme_dirs += [path.Path(theme).dirname().dirname().name]

        rofi_params = self.rofi_params(len(theme_dirs), 'gtk theme')
        try:
            selection = subprocess.run(
                self.menu.rofi_args(rofi_params),
                stdout=subprocess.PIPE,
                input=bytes('\n'.join(theme_dirs), 'UTF-8'),
                check=True
            ).stdout
        except CalledProcessError as proc_err:
            Misc.print_run_exception_info(proc_err)

        self.apply_settings(selection, '-a')

