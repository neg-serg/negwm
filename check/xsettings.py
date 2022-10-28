""" Change gtk / icons themes """
import os
import subprocess
import pathlib
import logging
import sys

from negwm.lib.misc import Misc

xdg_data_home=os.environ.get('XDG_DATA_HOME', '')
if not xdg_data_home:
    logging.error('Fatal! XDG_DATA_HOME is not set')
    sys.exit(1)


class xsettings():
    """ Change gtk / icons themes xsettingsd. """
    def __init__(self, menu):
        self.menu=menu
        self.xsettings_reload=os.path.expanduser('~/bin/xsettingsd-setup')

    def menu_params(self, prompt):
        """ Set menu params """
        return {'prompt': f'{self.menu.wrap_str(prompt)} {self.menu.conf("prompt")}'}

    def apply_settings(self):
        """ Apply selected gnome settings """
        try:
            subprocess.Popen([self.xsettings_reload])
        except subprocess.CalledProcessError as proc_err:
            Misc.print_run_exception_info(proc_err)

    def change_icon_theme(self):
        """ Changes icon theme with help of gsd-xsettings """
        icon_dirs=[]
        icons_path=pathlib.Path(f'{xdg_data_home}/icons').expanduser()
        for icon in icons_path.glob('*'):
            if icon:
                icon_dirs += [pathlib.Path(icon).name]
        menu_params=self.menu_params('icon theme')
        selection=''
        if not icon_dirs:
            return
        if len(icon_dirs) == 1:
            selection=icon_dirs[0]
        else:
            try:
                selection=subprocess.run(
                    self.menu.args(menu_params),
                    stdout=subprocess.PIPE,
                    input=bytes('\n'.join(icon_dirs), 'UTF-8'),
                    check=True
                ).stdout
            except subprocess.CalledProcessError as proc_err:
                Misc.print_run_exception_info(proc_err)
        if selection:
            self.apply_settings()

    def change_gtk_theme(self):
        """ Changes gtk theme with help of gsd-xsettings """
        theme_dirs=[]
        gtk_theme_path=pathlib.Path(f'{xdg_data_home}/themes').expanduser()
        for theme in gtk_theme_path.glob('*/*/gtk.css'):
            if theme:
                theme_dirs += [pathlib.PurePath(theme).parent.parent.name]
        menu_params=self.menu_params('gtk theme')
        selection=''
        if not theme_dirs:
            return

        if len(theme_dirs) == 1:
            selection=theme_dirs[0]
        else:
            try:
                selection=subprocess.run(
                    self.menu.args(menu_params),
                    stdout=subprocess.PIPE,
                    input=bytes('\n'.join(theme_dirs), 'UTF-8'),
                    check=True
                ).stdout
            except subprocess.CalledProcessError as proc_err:
                Misc.print_run_exception_info(proc_err)
        if selection:
            self.apply_settings()
