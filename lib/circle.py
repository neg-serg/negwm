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

from main import Matcher
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
        # Initialize superclasses.
        modi3cfg.__init__(self, i3, convert_me=True)
        Matcher.__init__(self)

        # most of initialization doing here.
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

        # current_position for the tag [tag]
        self.current_position = {}

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
            self.current_position[tag] = 0

        # tag all windows after start
        self.tag_windows()

        # store the current window here to cache get_tree().find_focused value.
        self.current_win = self.i3.get_tree().find_focused()

    def run_prog(self, tag, subtag=''):
        """ Run the appropriate application for the current tag/subtag.

        Args:
            tag (str): denotes target [tag]
            subtag (str): denotes the target [subtag], optional.
        """
        if tag is not None and self.cfg.get(tag) is not None:
            if not subtag:
                prog_str = self.extract_prog_str(self.conf(tag))
            else:
                prog_str = self.extract_prog_str(
                    self.conf(tag, subtag)
                )
            if prog_str:
                self.i3.command(f'exec {prog_str}')
            else:
                spawn_str = self.extract_prog_str(
                    self.conf(tag), "spawn", exe_file=False
                )
                if spawn_str:
                    self.i3.command(
                        f'exec ~/.config/i3/send executor run {spawn_str}'
                    )

    def find_next_not_the_same_win(self, tag):
        """ It was used as the guard to infinite loop in the past.
        Args:
            tag (str): denotes target [tag]
        """
        if len(self.tagged[tag]) > 1:
            self.current_position[tag] += 1
            self.go_next(tag)

    def prefullscreen(self, tag):
        """ Prepare to go fullscreen.
        """
        fullscreened = self.i3.get_tree().find_fullscreen()
        for win in fullscreened:
            if self.current_win.window_class in set(self.conf(tag, "class")) \
                    and self.current_win.id == win.id:
                self.need_handle_fullscreen = False
                win.command('fullscreen disable')

    def postfullscreen(self, tag, idx):
        """ Exit from fullscreen.
        """
        now_focused = self.twin(tag, idx).id
        for id in self.restore_fullscreen:
            if id == now_focused:
                self.need_handle_fullscreen = False
                self.i3.command(
                    f'[con_id={now_focused}] fullscreen enable'
                )

    def focus_next(self, tag, idx,
                   inc_counter=True,
                   fullscreen_handler=True,
                   subtagged=False):
        """ Focus next window. Used by go_next function.
        Tag list is a list of windows by some factor, which determined by
        config settings.

        Args:
            tag (str): target tag.
            idx (int): index inside tag list.
            inc_counter (bool): increase counter or not.
            fullscreen_handler (bool): for manual set / unset fullscreen,
                                        because of i3 is not perfect in it.
                                        For example you need it for different
                                        workspaces.
        """
        if fullscreen_handler:
            self.prefullscreen(tag)

        self.twin(tag, idx, subtagged).command('focus')

        if inc_counter:
            self.current_position[tag] += 1

        if fullscreen_handler:
            self.postfullscreen(tag, idx)

        self.need_handle_fullscreen = True

    def twin(self, tag, idx, with_subtag=False):
        """ Detect target window.
            Args:
                tag (str): selected tag.
                idx (int): index in tag list.
                with_subtag (bool): contains subtag, special behaviour then.
        """
        if not with_subtag:
            return self.tagged[tag][idx]
        else:
            subtag_win_classes = self.subtag_info.get("class", {})
            for subidx, win in enumerate(self.tagged[tag]):
                if win.window_class in subtag_win_classes:
                    return self.tagged[tag][subidx]

    def go_next(self, tag):
        """ Circle over windows. Function "called" from the user-side.

        Args:
            tag (str): denotes target [tag]
        """
        try:
            self.sort_by_parent(tag)
            if len(self.tagged[tag]) == 0:
                self.run_prog(tag)
            elif len(self.tagged[tag]) <= 1:
                idx = 0
                self.focus_next(tag, idx, fullscreen_handler=False)
            else:
                idx = self.current_position[tag] % len(self.tagged[tag])
                if ("priority" in self.conf(tag)) \
                        and self.current_win.window_class \
                        not in set(self.conf(tag, "class")):

                    if not len([win for win in self.tagged[tag]
                                if win.window_class ==
                                self.conf(tag, "priority")]):
                        self.run_prog(tag)
                        return

                    for idx, item in enumerate(self.tagged[tag]):
                        if item.window_class == self.conf(tag, "priority"):
                            fullscreened = self.i3.get_tree().find_fullscreen()
                            for win in fullscreened:
                                if win.window_class in self.conf(tag, "class") and \
                                        win.window_class != self.conf(tag, "priority"):
                                    self.interactive = False
                                    win.command('fullscreen disable')
                            self.focus_next(tag, idx, inc_counter=False)
                elif self.current_win.id == self.twin(tag, idx).id:
                    self.find_next_not_the_same_win(tag)
                else:
                    self.focus_next(tag, idx)
        except KeyError:
            self.tag_windows()
            self.go_next(tag)

    def go_subtag(self, tag, subtag):
        """ Circle over subtag windows. Function "called" from the user-side.

        Args:
            tag (str): denotes target [tag]
            subtag (str): denotes the target [subtag].
        """
        self.subtag_info = self.conf(tag, subtag)
        self.tag_windows()

        if self.subtag_info:
            subtagged_class_set = set(self.subtag_info.get("class", {}))
            tagged_win_classes = {
                w.window_class for w in self.tagged.get(tag, {})
            }
            if not (tagged_win_classes & subtagged_class_set):
                self.run_prog(tag, subtag)
            else:
                idx = 0
                self.focus_next(tag, idx, subtagged=True)

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
            "subtag": self.go_subtag,
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
                self.tagged.get(tag, {}).append(win)

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

    def sort_by_parent(self, tag):
        """
            Sort windows by some infernal logic: At first sort by parent
            container order, than in any order.

            Args:
                tag (str): target tag to sort.
        """
        parent_lst = []
        idx = 0

        try:
            for tag in self.cfg:
                if self.tagged[tag]:
                    for tagged_win in self.tagged[tag]:
                        if tagged_win.parent not in parent_lst:
                            for container_win in tagged_win.parent:
                                if container_win in self.tagged[tag]:
                                    oldidx = self.tagged[tag].index(
                                        container_win
                                    )
                                    self.tagged[tag].insert(
                                        idx, self.tagged[tag].pop(oldidx)
                                    )
                                    idx += 1
                        parent_lst.append(tagged_win.parent)
                else:
                    break
        except TypeError:
            pass

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
        self.subtag_info = {}
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

