""" Circle over windows module.

This is a module about better run-or-raise features like in ion3, stumpwm and
others. As the result user can get not only the usual run the appropriate
application if it is not started, but also create a list of application, which
I call "tag" and then switch to the next of it, instead of just simple focus.

The foundation of it is pretty complicated go_next function, which use counters
with incrementing of the current "position" of the window in the tag list over
the finite field. As the result you get circle over all tagged windows.

Also I've hacked fullscreen behaviour for it, so you can always switch to the
window with the correct fullscreen state, where normal i3 behaviour has a lot
of issues here in detection of existing/visible windows, etc.
"""

import re
import os
from modlib import Matcher
from modi3cfg import modi3cfg
from singleton import Singleton


class circle(modi3cfg, Matcher):
    """ Circle over windows class

    Parents:
        modi3cfg: configuration manager to autosave/autoload
                  TOML-configutation with inotify
        Matcher: class to check that window can be tagged with given tag by
                 WM_CLASS, WM_INSTANCE, regexes, etc

    Metaclass:
        Use Singleton metaclass from singleton module.

    """
    __metaclass__ = Singleton

    def __init__(self, i3, loop=None):
        """ Init function

        Main part is in self.initialize, which performs initialization itself.

        Args:
            i3: i3ipc connection
            loop: asyncio loop. It's need to be given as parameter because of
                  you need to bypass asyncio-loop to the thread
        """
        super().__init__(i3)
        self.initialize(i3)
        self.i3.on('window::new', self.add_wins)
        self.i3.on('window::close', self.del_wins)
        self.i3.on("window::focus", self.set_curr_win)
        self.i3.on("window::fullscreen_mode", self.handle_fullscreen)

    def initialize(self, i3):
        # i3ipc connection, bypassed by negi3mods runner.
        self.i3 = i3

        # map of tag to the tagged windows.
        self.tagged = {}

        # counters for the tag [tag]
        self.counters = {}

        # list of windows which fullscreen state need to be restored.
        self.restore_fullscreen = []

        # is the current action caused by user actions or not? It's needed for
        # corrent fullscreen on/off behaviour.
        self.interactive = True

        # how many attempts taken to find window with priority
        self.repeats = 0

        # winlist is used to reduce calling i3.get_tree() too many times.
        self.winlist = self.i3.get_tree()

        # used for subtag info caching
        self.subtag_info = {}

        # Should the special fullscreen-related actions to be performed or not.
        self.need_handle_fullscreen = True

        for tag in self.cfg:
            self.tagged[tag] = []
            self.counters[tag] = 0

        # tag all windows after start
        self.tag_windows()

        # store the current window here to cache get_tree().find_focused value.
        self.current_win = self.i3.get_tree().find_focused()

    def run_prog(self, tag, subtag=None):
        """ Run the appropriate application for the current tag/subtag.

        Args:
            tag (str): denotes target [tag]
            subtag (str): denotes the target [subtag], optional.
        """
        try:
            if subtag is None:
                prog_str = re.sub(
                    "~", os.path.realpath(os.path.expandvars("$HOME")),
                    self.cfg[tag]
                        .get("prog", {})
                )
            else:
                prog_str = re.sub(
                    "~", os.path.realpath(os.path.expandvars("$HOME")),
                    self.cfg[tag]
                        .get("prog_dict", {})
                        .get(subtag, {})
                        .get("prog", {})
                )
            if prog_str:
                self.i3.command('exec {}'.format(prog_str))
        except:
            pass

    def find_prioritized_win(self, tag):
        """ It was used as the guard to infinite loop in the past.

            TODO: need refactoring.

        Args:
            tag (str): denotes target [tag]
        """
        self.counters[tag] += 1
        self.repeats += 1
        if self.repeats < 8:
            self.go_next(tag)
        else:
            self.repeats = 0

    def go_next(self, tag, subtag=None):
        """ Circle over windows. Function "called" from the user-side.

            TODO: need refactoring to reduce cyclomatic complexity.

        Args:
            tag (str): denotes target [tag]
            subtag (str): denotes the target [subtag], optional.
        """
        def twin(with_subtag=False):
            if not with_subtag:
                return self.tagged[tag][idx]
            else:
                subtag_win_classes = self.subtag_info.get("includes", {})
                for subidx, win in enumerate(self.tagged[tag]):
                    if win.window_class in subtag_win_classes:
                        return self.tagged[tag][subidx]

        def focus_next(inc_counter=True, fullscreen_handler=True, subtag=None):
            if fullscreen_handler:
                fullscreened = self.i3.get_tree().find_fullscreen()
                for win in fullscreened:
                    if self.current_win.window_class in set(self.cfg[tag]["class"]) \
                            and self.current_win.id == win.id:
                        self.need_handle_fullscreen = False
                        win.command('fullscreen disable')

            twin(subtag is not None).command('focus')

            if inc_counter:
                self.counters[tag] += 1

            if fullscreen_handler:
                now_focused = twin().id
                for id in self.restore_fullscreen:
                    if id == now_focused:
                        self.need_handle_fullscreen = False
                        self.i3.command(
                            f'[con_id={now_focused}] fullscreen enable'
                        )

            self.need_handle_fullscreen = True

        try:
            if subtag is None:
                if len(self.tagged[tag]) == 0:
                    self.run_prog(tag)
                elif len(self.tagged[tag]) <= 1:
                    idx = 0
                    focus_next(fullscreen_handler=False)
                else:
                    idx = self.counters[tag] % len(self.tagged[tag])

                    if ("priority" in self.cfg[tag]) \
                            and self.current_win.window_class \
                            not in set(self.cfg[tag]["class"]):

                        if not len([win for win in self.tagged[tag]
                                    if win.window_class ==
                                    self.cfg[tag]["priority"]]):
                            self.run_prog(tag)
                            return

                        for idx, item in enumerate(self.tagged[tag]):
                            if item.window_class == self.cfg[tag]["priority"]:
                                fullscreened = \
                                    self.i3.get_tree().find_fullscreen()
                                for win in fullscreened:
                                    tgt = self.cfg[tag]
                                    if win.window_class in tgt["class"] \
                                            and win.window_class != tgt["priority"]:
                                        self.interactive = False
                                        win.command('fullscreen disable')
                                focus_next(inc_counter=False)
                                return
                    elif self.current_win.id == twin().id:
                        self.find_prioritized_win(tag)
                    else:
                        focus_next()
            else:
                self.subtag_info = \
                    self.cfg[tag].get("prog_dict", {}).get(subtag, {})
                if not len(set(self.subtag_info.get("includes", {})) &
                           {w.window_class for w in self.tagged[tag]}):
                    self.run_prog(tag, subtag)
                else:
                    idx = 0
                    focus_next(fullscreen_handler=False, subtag=subtag)
        except KeyError:
            self.tag_windows()
            self.go_next(tag)

    def switch(self, args):
        """ Defines pipe-based IPC for cirled module. With appropriate
            function bindings.

            This function defines bindings to the named_scratchpad methods that
            can be used by external users as i3-bindings, sxhkd, etc. Need the
            [send] binary which can send commands to the appropriate FIFO.

            Args:
                args (List): argument list for the selected function.
        """
        {
            "next": self.go_next,
            "run": self.go_next,
            "add_prop": self.add_prop,
            "del_prop": self.del_prop,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def add_prop(self, tag, prop_str):
        """ Add property via [prop_str] to the target [tag].

        Args:
            tag (str): denotes the target tag.
            prop_str (str): string in i3-match format used to add/delete
                            target window in/from scratchpad.
        """
        if tag in self.cfg:
            self.add_props(tag, prop_str)

        for t in self.cfg:
            if t != tag:
                self.del_props(t, prop_str)

        self.initialize(self.i3)

    def del_prop(self, tag, prop_str):
        """ Delete property via [prop_str] to the target [tag].

            Args:
                tag (str): denotes the target tag.
                prop_str (str): string in i3-match format used to add/delete
                                target window in/from scratchpad.
        """
        self.del_props(tag, prop_str)

    def find_acceptable_windows(self, tag):
        """ Wrapper over Matcher.match to find acceptable windows and add it to
            tagged[tag] list.

            Args:
                tag (str): denotes the target tag.
        """
        for win in self.winlist.leaves():
            if self.match(win, tag):
                self.tagged[tag].append(win)

    def tag_windows(self):
        """ Find acceptable windows for the all tags and add it to the
            tagged[tag] list.

            Args:
                tag (str): denotes the target tag.
        """
        self.winlist = self.i3.get_tree()
        self.tagged = {}

        for tag in self.cfg:
            self.tagged[tag] = []

        for tag in self.cfg:
            self.find_acceptable_windows(tag)

    def add_wins(self, i3, event):
        """ Tag window if it is match defined rules.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        win = event.container
        for tag in self.cfg:
            if self.match(win, tag):
                try:
                    self.tagged[tag].append(win)
                except KeyError:
                    self.tag_windows()
                    self.add_wins(i3, event)
        self.winlist = self.i3.get_tree()

    def del_wins(self, i3, event):
        """ Delete tag from window if it's closed.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        win = event.container
        for tag in self.cfg:
            if self.match(win, tag):
                try:
                    if self.tagged[tag] is not None:
                        for win in self.tagged[tag]:
                            if win.id in self.restore_fullscreen:
                                self.restore_fullscreen.remove(win.id)
                    del self.tagged[tag]
                except KeyError:
                    self.tag_windows()
                    self.del_wins(i3, event)
        self.winlist = self.i3.get_tree()

    def set_curr_win(self, i3, event):
        """ Cache the current window.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        self.current_win = event.container

    def handle_fullscreen(self, i3, event):
        """ Performs actions over the restore_fullscreen list.

            This function memorize the current state of the fullscreen property
            of windows for the future reuse it in functions which need to
            set/unset fullscreen state of the window correctly.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        win = event.container
        if self.need_handle_fullscreen:
            if win.fullscreen_mode:
                if win.id not in self.restore_fullscreen:
                    self.restore_fullscreen.append(win.id)
                    return
            if not win.fullscreen_mode:
                if win.id in self.restore_fullscreen:
                    self.restore_fullscreen.remove(win.id)
                    return

