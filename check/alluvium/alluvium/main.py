import argparse
import atexit
import os
import signal
import sys
import tempfile
from pathlib import Path
from threading import Thread

from i3ipc import Connection, Event

from .config import Config
from .overlay import Overlay

import gi  # isort:skip

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # isort:skip


def listen_for_mode_change(i3, handler):
    def on_mode_change(_, event):
        new_mode = event.change
        GLib.idle_add(handler, new_mode)

    i3.on(Event.MODE, on_mode_change)

    i3.main()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hide",
        default=False,
        action="store_true",
        help="Stop a running alluvium instance",
    )
    parser.add_argument(
        "--toggle", default=False, action="store_true", help="Toggle alluvium on/off"
    )
    parser.add_argument("-m", "--mode", default="default", help="Initial mode to show")
    parser.add_argument(
        "--quit-on-default",
        default=False,
        action="store_true",
        help="Quit when returning to default mode",
    )
    args = parser.parse_args()

    hide = args.hide
    toggle = args.toggle
    initial_mode = args.mode
    quit_on_default = args.quit_on_default

    pid_file = Path(tempfile.gettempdir()) / "alluvium.pid"

    if hide:
        if pid_file.is_file():
            os.kill(int(pid_file.read_text()), signal.SIGINT)
        sys.exit(0)
    elif toggle:
        if pid_file.is_file():
            os.kill(int(pid_file.read_text()), signal.SIGINT)
            sys.exit(0)
    else:
        # Never run a second instance on top of another one
        if pid_file.is_file():
            sys.exit(0)

    i3 = Connection()
    config_reply = i3.get_config()
    config = Config.from_data(config_reply.config)

    overlay = Overlay()
    overlay.show_bindings(initial_mode, config)

    def quit(*args):
        i3.main_quit()
        Gtk.main_quit()

    def on_mode_change(mode):
        if mode == "default" and quit_on_default:
            quit()
        else:
            overlay.show_bindings(mode, config)

    # Update the overlay when i3 changes its mode
    thread = Thread(
        name="thread-i3",
        target=listen_for_mode_change,
        args=(i3, on_mode_change),
        daemon=False,
    )
    thread.start()

    overlay.window.connect("destroy", quit)
    signal.signal(signal.SIGINT, lambda *args: quit())

    def cleanup_pid_file():
        pid_file.unlink(missing_ok=True)

    atexit.register(cleanup_pid_file)

    pid_file.write_text(str(os.getpid()))
    Gtk.main()
