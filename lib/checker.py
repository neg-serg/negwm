import os
import shutil
import subprocess
import logging
from lib.misc import Misc

class checker():
    @staticmethod
    def which(exe, description, kind):
        path = shutil.which(exe)
        if path:
            logging.info(f'{exe}: {shutil.which(exe)} [{kind}] [OK]')
        else:
            logging.error(f'{exe}: {exe} not found [{kind}] [FAIL]\n'
                    f'You need it for {description}')
            if kind == 'mandatory':
                logging.error('You cannot run without mandatory dependencies')
                os._exit(1)

    @staticmethod
    def check_for_executable_deps():
        dependencies = {
            'mandatory' : {
                'i3': 'you need i3 for negwm',
                'dash': 'one of the fastest non-interactive shells',
            },
            'recommended' : {
                'tmux': 'tmux support',
                'rofi': 'you need rofi for the all menus',
                'dunst': 'you need dunst for notifications',
                'dunstify': 'dunstify is better notify-send alternative',
                'xdo': 'optional polybar hide support instead of built-in',
                'zsh': 'use zsh as one of the best interactive shells',
                'alacritty': 'alacritty is recommended as default shell',
                'pactl': 'you need pactl for pulsectl menu',
            }
        }

        logging.info('Check for executables')
        for kind, value in dependencies.items():
            for exe, description in value.items():
                checker.which(exe, description, kind)

    @staticmethod
    def check_i3_config(cfg='config'):
        logging.info('Check for i3 config consistency')
        i3_cfg = f'{os.environ["XDG_CONFIG_HOME"]}/i3/{cfg}'
        if not (os.path.isfile(i3_cfg) and \
                os.path.getsize(i3_cfg) > 0):
            logging.error(f'There is no target i3 config file in {i3_cfg}, fail')
            os._exit(1)

        i3_check = Misc.validate_i3_config(i3_cfg)
        if i3_check:
            logging.info('i3 config is valid [OK]')
        else:
            logging.error('i3 config is invalid [FAIL]'
                f'please run i3 -C {Misc.negwm_path()}/{cfg} to check it'
            )
            os._exit(1)
        return True

    @staticmethod
    def check_env():
        logging.info('Check for environment')
        xdg_config_home = os.getenv('XDG_CONFIG_HOME')
        if xdg_config_home:
            logging.info(f'XDG_CONFIG_HOME = {xdg_config_home}')
        else:
            user = os.getenv('USER')
            if user:
                logging.error('XDG_CONFIG_HOME is unset, '
                    'you should set it via some kind of '
                    '.zshenv or /etc/profile')
            else:
                logging.error('You should have some $USER env to run')
                os._exit(1)

    @staticmethod
    def check():
        """ Check for various dependencies """
        logging.basicConfig(level=logging.ERROR)
        checker.check_env()
        checker.check_for_executable_deps()
        checker.check_i3_config()
