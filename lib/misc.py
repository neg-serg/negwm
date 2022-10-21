""" Various helper functions Class for this is created for the more well
defined namespacing and more simple import. """
import os
import subprocess
import errno
import re
import logging
from typing import List

try:
    from xdg import xdg_config_home
    xdg_config_home = str(xdg_config_home())
except ImportError:
    from xdg.BaseDirectory import xdg_config_home


class Misc():
    ''' Implements various helper functions '''
    @staticmethod
    def create_dir(dirname) -> None:
        ''' Helper function to create directory
            dirname(str): directory name to create '''
        if os.path.isdir(dirname):
            return
        try:
            logging.info(f'Creating dir {dirname}')
            os.makedirs(dirname)
        except OSError as oserr:
            if oserr.errno != errno.EEXIST:
                raise

    @staticmethod
    def xdg_config_home() -> str:
        return xdg_config_home

    @staticmethod
    def negwm_path() -> str:
        ''' Easy way to return negwm config path. '''
        current_dir=os.path.dirname(__file__)
        return f'{current_dir}/../'

    @staticmethod
    def lib_path() -> str:
        ''' Easy way to return negwm library path. '''
        current_dir=os.path.dirname(__file__)
        libdir_env=os.environ.get('NEGWM_LIB', '')
        if libdir_env:
            return libdir_env
        else:
            return current_dir

    @staticmethod
    def cfg_path() -> str:
        ''' Easy way to return negwm configurations path. '''
        current_dir=os.path.dirname(__file__)
        cfgdir_env=os.environ.get('NEGWM_CFG', '')
        if cfgdir_env:
            return cfgdir_env
        else:
            return f'{current_dir}/../cfg/'

    @staticmethod
    def cache_path() -> str:
        ''' Easy way to return negwm cache path. '''
        current_dir=os.path.dirname(__file__)
        cfgdir_env=os.environ.get('NEGWM_CACHE', '')
        cache_home=os.environ.get('XDG_CACHE_HOME', '')
        fallback_cache_path=f'{current_dir}/../cache/'
        if cache_home:
            Misc.create_dir(cache_home)
            return f'{cache_home}/negwm'
        elif cfgdir_env:
            Misc.create_dir(cfgdir_env)
            return cfgdir_env
        else:
            Misc.create_dir(fallback_cache_path)
            return fallback_cache_path

    @staticmethod
    def i3path() -> str:
        ''' Easy way to return i3 config path. '''
        cfg_home=Misc.xdg_config_home()
        Misc.create_dir(f'{cfg_home}/i3')
        return os.path.expanduser(f'{cfg_home}/i3')

    @staticmethod
    def i3_cfg_try_create() -> bytes:
        return subprocess.check_output(['i3-config-wizard', '-m', 'win'])

    @staticmethod
    def i3_cfg_need_dump() -> bool:
        i3_config_wizard_pie='# This file has been auto-generated by i3-config-wizard'
        negwm_config_pie='# [Generated by negwm]\n'
        with open(Misc.current_i3_cfg()) as f:
            first_line=f.readline()
            if i3_config_wizard_pie in first_line or \
                negwm_config_pie not in first_line:
                return True
        return False

    @staticmethod
    def current_i3_cfg() -> str:
        def find_between(s, start, end):
            return (s.split(start))[1].split(end)[0]
        return find_between(str(Misc.i3_cfg_try_create()), 'file "', '" already')

    @staticmethod
    def print_run_exception_info(proc_err) -> None:
        logging.info(f'returncode={proc_err.returncode}, \
                cmd={proc_err.cmd}, \
                output={proc_err.output}')

    @staticmethod
    def parse_attr(attrib_list: List, end='"] ') -> str:
        ''' Create attribute matching string.
            tag (str): target tag.
            attr (str): target attrubute. '''
        ret = ''
        if len(attrib_list) > 1:
            ret += '('
        for i, item in enumerate(attrib_list):
            ret += item
            if i + 1 < len(attrib_list):
                ret += '|'
        if len(attrib_list) > 1:
            ret += ')$'
        ret += end
        return ret

    @staticmethod
    def validate_i3_config(conf_gen_path, remove=False) -> bool:
        ''' Checks that i3 config is ok. '''
        check_config=""
        try:
            check_config=subprocess.run(
                ['i3', '-c', conf_gen_path, '-C'],
                stdout=subprocess.PIPE,
                check=True
            ).stdout.decode('utf-8')
        except subprocess.CalledProcessError as proc_err:
            Misc.print_run_exception_info(proc_err)
        if check_config:
            error_data=check_config.encode('utf-8')
            logging.error(error_data)
            if remove:
                os.remove(conf_gen_path)  # remove invalid config
            return False
        return True

    @staticmethod
    def extract_prog_str(conf_part: dict,
                         prog_field: str = "prog",
                         exe_file: bool = True) -> str:
        ''' Helper to extract prog(by default) string from config
            conf_part (dict): part of config from where you want to extract it.
            prog_field (str): string name to extract.
        '''
        if conf_part is None:
            return ''
        conf_part.setdefault(prog_field, '')
        if exe_file:
            return re.sub(
                '~',
                os.path.realpath(os.path.expandvars("$HOME")),
                conf_part[prog_field]
            )
        return conf_part[prog_field]
