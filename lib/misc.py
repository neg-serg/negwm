""" Various helper functions Class for this is created for the more well
defined namespacing and more simple import. """
import os
import subprocess
import errno
import re
import logging
from typing import List

from extension import extension


class Misc():
    """ Implements various helper functions """
    @staticmethod
    def create_dir(dirname) -> None:
        """ Helper function to create directory
            dirname(str): directory name to create """
        try:
            os.makedirs(dirname)
        except OSError as oserr:
            if oserr.errno != errno.EEXIST:
                raise

    @staticmethod
    def i3path() -> str:
        """ Easy way to return i3 config path. """
        cfg_home = ''
        cfg_home = os.path.expandvars("$XDG_CONFIG_HOME")
        if cfg_home == "$XDG_CONFIG_HOME":
            cfg_home = os.path.expanduser("~/.config")
        if not os.path.exists(f"{cfg_home}/negwm"):
            os.makedirs(cfg_home)
        return os.path.expanduser(f"{cfg_home}/negwm")

    @staticmethod
    def echo_on(*args, **kwargs) -> None:
        """ Print info """
        logging.info(*args, **kwargs)

    @staticmethod
    def echo_off(*_dummy_args, **_dummy_kwargs) -> None:
        """ Do not print info """
        return

    @staticmethod
    def print_run_exception_info(proc_err) -> None:
        logging.info(f'returncode={proc_err.returncode}, \
                cmd={proc_err.cmd}, \
                output={proc_err.output}')

    @staticmethod
    def parse_attr(attrib_list: List, end='"] ') -> str:
        """ Create attribute matching string.
            tag (str): target tag.
            attr (str): target attrubute. """
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
    def ch(lst: List, ch: str) -> str:
        """ Return char is list is not empty to prevent stupid commands. """
        ret = ''
        if len(lst) > 1:
            ret = ch
        return ret

    @staticmethod
    def validate_i3_config(conf_gen_path, remove=False) -> bool:
        """ Checks that i3 config is ok. """
        check_config = ""
        try:
            check_config = subprocess.run(
                ['i3', '-c', conf_gen_path, '-C'],
                stdout=subprocess.PIPE,
                check=True
            ).stdout.decode('utf-8')
        except subprocess.CalledProcessError as proc_err:
            Misc.print_run_exception_info(proc_err)
        if check_config:
            error_data = check_config.encode('utf-8')
            logging.error(error_data)
            if remove:
                os.remove(conf_gen_path)  # remove invalid config
            return False
        return True

    @staticmethod
    def extract_prog_str(conf_part: dict,
                         prog_field: str = "prog",
                         exe_file: bool = True) -> str:
        """ Helper to extract prog(by default) string from config
            conf_part (dict): part of config from where you want to extract it.
            prog_field (str): string name to extract.
        """
        if conf_part is None:
            return ""
        if exe_file:
            return re.sub(
                "~",
                os.path.realpath(os.path.expandvars("$HOME")),
                conf_part.get(prog_field, "")
            )
        return conf_part.get(prog_field, "")

class Rules():
    @staticmethod
    def fill_rules_dict(mod, cmd_dict) -> List:
        config = mod.cfg
        for tag in config:
            cmd_dict[tag] = []
            for attr in config[tag]:
                for fill in ['classw', 'instance', 'name', 'role']:
                    cmd_dict[tag].append(Rules.info(config, tag, attr, fill))
        return cmd_dict

    @staticmethod
    def rules_mod(modname):
        """ Create i3 match rules for all tags. """
        ret = ''
        mods = extension.get_mods()
        if mods is None or not mods:
            return ret
        mod = mods.get(modname, None)
        if mod is None:
            return ''
        cmd_dict = Rules.fill_rules_dict(mod, {})
        for tag in cmd_dict:
            rules = list(filter(lambda str: str != '', cmd_dict[tag]))
            if rules:
                ret += f'set ${modname}-{tag} [' + ' '.join(rules) + ']\n'
        return (ret, cmd_dict, mod)

    @staticmethod
    def info(config: dict, tag: str, attr: str, fill: str) -> str:
        """ Create rule in i3 commands format
            config (dict): extension config.
            tag (str): target tag.
            attr (str): tag attrubutes.
            fill (str): attribute to fill. """
        conv_dict_attr = {
            'classw': 'class',
            'instance': 'instance',
            'name': 'window_name',
            'role': 'window_role'
        }
        cmd = ''
        if fill in attr:
            if not attr.endswith('_r'):
                win_attr = conv_dict_attr[attr]
            else:
                win_attr = conv_dict_attr[attr[:-2]]
            start = f'{win_attr}="' + Misc.ch(config[tag][attr], '^')
            attrlist = []
            attrlist = config[tag][attr]
            if config[tag].get(attr + '_r', ''):
                attrlist += config[tag][attr + '_r']
            if not attr.endswith('_r'):
                cmd = start + Misc.parse_attr(attrlist, end='')
            if cmd:
                cmd += '"'
        return cmd
