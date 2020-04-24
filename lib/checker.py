import os
import shutil
import subprocess

from lib.misc import Misc

class checker():
    @staticmethod
    def which(exe, description, kind, verbose):
        path = shutil.which(exe)
        if path:
            if verbose:
                print(f'{exe}: {shutil.which(exe)} [{kind}] [OK]')
        else:
            print(f'{exe}: {exe} not found [{kind}] [FAIL]\n'
                    f'You need it for {description}')

            if kind == 'mandatory':
                print('You cannot run without mandatory dependencies')
                os._exit(1)

    @staticmethod
    def check_for_executable_deps(verbose):
        dependencies = {
            'mandatory' : {
                'i3': 'you need i3 for negi3wm',
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
                'pulseaudio': 'you need pulseaudio for pulsectl menu',
            }
        }

        if verbose:
            print('Check for executables')
        for kind, value in dependencies.items():
            for exe, description in value.items():
                checker.which(exe, description, kind, verbose)

    @staticmethod
    def check_for_send(verbose):
        if verbose:
            print('Check for send executable and build it if needed')
        send_path = shutil.which('bin/send')
        if send_path is not None:
            if verbose:
                print(f'send binary {send_path} [OK]')
        else:
            i3_path = os.getenv('XDG_CONFIG_HOME') + '/i3/'
            make_result = subprocess.run(['make', '-C', i3_path],
                check=False,
                capture_output=True
            )
            if make_result.returncode == 0:
                print('send build is successful')
            else:
                print('Please check for libbsd-dev build dependency')

    @staticmethod
    def check_i3_config(verbose, cfg='config'):
        if verbose:
            print('Check for i3 config consistency')
        i3_cfg = f'{Misc.i3path()}/{cfg}'
        if not (os.path.isfile(i3_cfg) and \
                os.path.getsize(i3_cfg) > 0):
            print(f'There is no target i3 config file in {i3_cfg}, fail')
            os._exit(1)

        i3_check = Misc.validate_i3_config(i3_cfg)
        if i3_check:
            if verbose:
                print('i3 config is valid [OK]')
        else:
            print('i3 config is invalid [FAIL]'
                f'please run i3 -C {Misc.i3path()}/{cfg} to check it'
            )
            os._exit(1)
        return True

    @staticmethod
    def check_env(verbose):
        if verbose:
            print('Check for environment')
        xdg_config_home = os.getenv('XDG_CONFIG_HOME')
        if xdg_config_home:
            if verbose:
                print(f'XDG_CONFIG_HOME = {xdg_config_home}')
        else:
            user = os.getenv('USER')
            if user:
                print('XDG_CONFIG_HOME is unset, '
                    'you should set it via some kind of '
                    '.zshenv or /etc/profile')
            else:
                print('You should have some $USER env to run')
                os._exit(1)

    @staticmethod
    def check(verbose):
        """ Check for various dependencies """
        checker.check_env(verbose)
        checker.check_for_executable_deps(verbose)
        checker.check_i3_config(verbose)
        checker.check_for_send(verbose)
