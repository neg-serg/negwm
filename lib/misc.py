""" Various helper functions

    Class for this is created for the more well defined namespacing and more
    simple import.
"""
import os
import subprocess
import errno


class Misc():
    """ Implements various helper functions
    """

    @staticmethod
    def create_dir(dirname):
        """ Helper function to create directory

            Args:
                dirname(str): directory name to create
        """
        try:
            os.makedirs(dirname)
        except OSError as oserr:
            if oserr.errno != errno.EEXIST:
                raise

    @staticmethod
    def i3path() -> str:
        """ Easy way to return i3 config path.
        """
        return os.environ.get("XDG_CONFIG_HOME") + "/i3/"

    @staticmethod
    def extract_xrdb_value(field: str) -> str:
        """ Extracts field from xrdb executable.
        """
        out = subprocess.run(
            f"xrescat '{field}'",
            shell=True,
            stdout=subprocess.PIPE
        ).stdout
        if out is not None and out:
            ret = out.decode('UTF-8').split()[0]
            return ret
        return ""

    @classmethod
    def notify_msg(cls, msg: str, prefix: str = " "):
        """ Send messages via notify-osd based notifications.

            Args:
                msg: message string.
                prefix: optional prefix for message string.
        """

        def get_pids(process):
            try:
                pidlist = map(
                    int, subprocess.check_output(["pidof", process]).split()
                )
            except subprocess.CalledProcessError:
                pidlist = []
            return pidlist

        if get_pids('dunst'):
            foreground_color = cls.extract_xrdb_value('\\*.foreground')
            notify_msg = [
                'dunstify', '',
                f"<span weight='normal' color='{foreground_color}'>" +
                prefix + msg +
                "</span>"
            ]
            subprocess.Popen(notify_msg)

    @classmethod
    def notify_off(cls, _dummy_msg: str, _dummy_prefix: str = " "):
        """ Do nothing """
        return

    @staticmethod
    def echo_on(*args, **kwargs):
        """ print info """
        print(*args, **kwargs)

    @staticmethod
    def echo_off(*_dummy_args, **_dummy_kwargs):
        """ do not print info """
        return

    @staticmethod
    def print_run_exception_info(proc_err):
        print(f'returncode={proc_err.returncode}, \
                cmd={proc_err.cmd}, \
                output={proc_err.output}')
