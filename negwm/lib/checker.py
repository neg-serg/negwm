""" NegWM health-checker """
import os
import subprocess
import shutil
import logging
from negwm.lib.misc import Misc

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
                'dunst': 'you need dunst for notifications',
                'dunstify': 'dunstify is better notify-send alternative',
                'pactl': 'you need pactl for pulsectl menu',
                'rofi': 'you need rofi for the all menus',
                'tmux': 'tmux support',
                'xdo': 'optional polybar hide support instead of built-in',
            }
        }

        logging.info('Check for executables')
        for kind, value in dependencies.items():
            for exe, description in value.items():
                checker.which(exe, description, kind)

    @staticmethod
    def check_i3_config(cfg='config') -> bool:
        logging.info('Check for i3 config consistency')
        
        subprocess.check_output(["i3-config-wizard", "-m", "win"])
        current_i3_config = Misc.current_i3_cfg()
        if not (os.path.isfile(current_i3_config) and \
                os.path.getsize(current_i3_config) > 0):
            logging.error(f'There is no target i3 config file in {current_i3_config}, fail')
            return False

        cfg_to_check = f'{os.path.dirname(current_i3_config)}/{cfg}'
        i3_check = Misc.validate_i3_config(cfg_to_check)
        if i3_check:
            logging.info('i3 config is valid [OK]')
        else:
            logging.error('i3 config is invalid [FAIL]'
                f'please run i3 -c {cfg_to_check} -C to check it'
            )
            return False
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

    @staticmethod
    def check():
        """ Check for various dependencies """
        logging.basicConfig(level=logging.ERROR)
        checker.check_env()
        checker.check_for_executable_deps()
        checker.check_i3_config()
