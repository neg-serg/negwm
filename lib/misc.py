""" Various helper functions Class for this is created for the more well
defined namespacing and more simple import. """
import os
import subprocess
import errno
import functools
import operator
import re
from typing import List


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
        if not os.path.exists(f"{cfg_home}/negi3wm"):
            os.makedirs(cfg_home)
        return os.path.expanduser(f"{cfg_home}/negi3wm")

    @staticmethod
    def echo_on(*args, **kwargs) -> None:
        """ Print info """
        print(*args, **kwargs)

    @staticmethod
    def echo_off(*_dummy_args, **_dummy_kwargs) -> None:
        """ Do not print info """
        return

    @staticmethod
    def print_run_exception_info(proc_err) -> None:
        print(f'returncode={proc_err.returncode}, \
                cmd={proc_err.cmd}, \
                output={proc_err.output}')

    @staticmethod
    def send(*args, i3=None) -> None:
        """ Send wrapper """
        send_path = Misc.i3path() + '/bin/send'
        if i3 is None:
            try:
                subprocess.run([send_path] + list(args), check=True)
            except subprocess.CalledProcessError as proc_err:
                Misc.print_run_exception_info(proc_err)
        else:
            exec_cmd = 'exec ' + send_path + ' '
            largs = functools.reduce(operator.iconcat, list(args), [])
            i3.command(exec_cmd + ' '.join(largs))

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
            print(error_data)
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
