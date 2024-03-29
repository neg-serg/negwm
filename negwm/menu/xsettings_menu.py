#!/usr/bin/env python
""" Change gtk / icons themes """
import os
import subprocess
import pathlib
import logging
import sys
import fileinput
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

xdg_data_home=os.environ.get('XDG_DATA_HOME', '')
if not xdg_data_home:
    logging.error('Fatal! XDG_DATA_HOME is not set')
    sys.exit(1)


@staticmethod
def print_run_exception_info(proc_err):
    logging.info(f'returncode={proc_err.returncode}, \
                    cmd={proc_err.cmd}, \
                    output={proc_err.output}')

class xsettings():
    """ Change gtk / icons themes xsettingsd. """
    setup=os.path.expanduser('~/bin/xsettingsd-setup').split()
    def __init__(self):
        self.prompt='❯>'

    def menu_params(self, prompt: str):
        """ Set menu params """
        return {'prompt': f'{menu.wrap_str(prompt)} {self.prompt}'}

    def apply_settings(self, param: str, selection: str):
        """ Apply selected gnome settings """
        try:
            path=os.path.expanduser('~/bin/xsettingsd')
            match param:
                case 'theme': param='Net/ThemeName'
                case 'icon': param='Net/IconThemeName'
                case _: return 'Wrong param'
            with fileinput.FileInput(path, inplace=True, backup='.bck') as settings:
                for line in settings:
                    if not param in line:
                        print(line, end='')
                    else:
                        print(line.replace(line, f'{param} "{selection.strip()}"'), end='\n')
            subprocess.Popen(xsettings.setup)
        except subprocess.CalledProcessError as proc_err:
            print_run_exception_info(proc_err)

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
                    menu.args(menu_params),
                    stdout=subprocess.PIPE,
                    input=bytes('\n'.join(icon_dirs), 'UTF-8'),
                    check=True
                ).stdout
            except subprocess.CalledProcessError as proc_err:
                print_run_exception_info(proc_err)
        if selection:
            self.apply_settings('icon', selection.decode('utf-8'))

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
                    menu.args(menu_params),
                    stdout=subprocess.PIPE,
                    input=bytes('\n'.join(theme_dirs), 'UTF-8'),
                    check=True
                ).stdout
            except subprocess.CalledProcessError as proc_err:
                print_run_exception_info(proc_err)
        if selection:
            self.apply_settings('theme', selection.decode('utf-8'))

def main():
    if len(sys.argv) > 1:
        match sys.argv[1]:
            case 'gtk': xsettings().change_gtk_theme()
            case 'icon': xsettings().change_icon_theme()
    else:
        xsettings().change_gtk_theme()

if __name__ == '__main__':
    main()
