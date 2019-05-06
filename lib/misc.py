import os
import subprocess
import errno


class Misc():
    @staticmethod
    def create_dir(dirname):
        try:
            os.makedirs(dirname)
        except OSError as e:
            if e.errno != errno.EEXIST:
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
            f"xrdb -query | rg '{field}' | awk '{{print $2}}'",
            shell=True,
            stdout=subprocess.PIPE
        ).stdout
        if out is not None and out:
            ret = out.decode('UTF-8').split()[0]
            return ret

    @classmethod
    def notify_msg(cls, msg: str, prefix: str = " "):
        """ Send messages via notify-osd based notifications.

            Args:
                msg: message string.
                prefix: optional prefix for message string.
        """
        foreground_color = cls.extract_xrdb_value('\\*.foreground')
        notify_msg = [
            'notify-send',
            f"<span weight='normal' color='{foreground_color}'>" +
            prefix + msg +
            "</span>"
        ]
        subprocess.Popen(notify_msg)

