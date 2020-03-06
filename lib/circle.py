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

from misc import Misc
from negi3mod import negi3mod
from matcher import Matcher
from cfg import cfg


class circle(negi3mod, cfg, Matcher):
    """ Circle over windows class

    Parents:
        cfg: configuration manager to autosave/autoload
             TOML-configutation with inotify
        Matcher: class to check that window can be tagged with given tag by
                 WM_CLASS, WM_INSTANCE, regexes, etc

    """

    def __init__(self, i3) -> None:
        """ Init function

        Main part is in self.initialize, which performs initialization itself.

        Args:
            i3: i3ipc connection
        """
        # Initialize superclasses.
        cfg.__init__(self, i3, convert_me=True)
        Matcher.__init__(self)

        # i3ipc connection, bypassed by negi3mods runner.
        self.i3ipc = i3

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

        # win cache for the fast matching
        self.win = None

        # used for subtag info caching
        self.subtag_info = {}

        # Should the special fullscreen-related actions to be performed or not.
        self.need_handle_fullscreen = True

        # Initialize
        i3tree = self.i3ipc.get_tree()

        # prepare for prefullscreen
        self.fullscreened = i3tree.find_fullscreen()

        # store the current window here to cache get_tree().find_focused value.
        self.current_win = i3tree.find_focused()

        # winlist is used to reduce calling i3.get_tree() too many times.
        self.winlist = i3tree.leaves()
        for tag in self.cfg:
            self.tagged[tag] = []
            self.current_position[tag] = 0

        # tag all windows after start
        self.tag_windows(invalidate_winlist=False)

        self.bindings = {
            "next": self.go_next,
            "subtag": self.go_subtag,
            "add_prop": self.add_prop,
            "del_prop": self.del_prop,
            "reload": self.reload_config,
        }

        self.i3ipc.on('window::new', self.add_wins)
        self.i3ipc.on('window::close', self.del_wins)
        self.i3ipc.on("window::focus", self.set_curr_win)
        self.i3ipc.on("window::fullscreen_mode", self.handle_fullscreen)

    def run_prog(self, tag: str, subtag: str = '') -> None:
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
                self.i3ipc.command(f'exec {prog_str}')
            else:
                spawn_str = self.extract_prog_str(
                    self.conf(tag), "spawn", exe_file=False
                )
                if spawn_str:
                    Misc.send(f'executor run {spawn_str}', i3=self.i3ipc)

    def find_next_not_the_same_win(self, tag: str) -> None:
        """ It was used as the guard to infinite loop in the past.
        Args:
            tag (str): denotes target [tag]
        """
        if len(self.tagged[tag]) > 1:
            self.current_position[tag] += 1
            self.go_next(tag)

    def prefullscreen(self, tag: str) -> None:
        """ Prepare to go fullscreen.
        """
        for win in self.fullscreened:
            if self.current_win.window_class in set(self.conf(tag, "class")) \
                    and self.current_win.id == win.id:
                self.need_handle_fullscreen = False
                win.command('fullscreen disable')

    def postfullscreen(self, tag: str, idx: int) -> None:
        """ Exit from fullscreen.
        """
        now_focused = self.twin(tag, idx).id
        for win_id in self.restore_fullscreen:
            if win_id == now_focused:
                self.need_handle_fullscreen = False
                self.i3ipc.command(
                    f'[con_id={now_focused}] fullscreen enable'
                )

    def focus_next(self, tag: str, idx: int,
                   inc_counter: bool = True,
                   fullscreen_handler: bool = True,
                   subtagged: bool = False) -> None:
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
            subtagged (bool): this flag denotes to subtag using.
        """
        if fullscreen_handler:
            self.prefullscreen(tag)

        self.twin(tag, idx, subtagged).command('focus')

        if inc_counter:
            self.current_position[tag] += 1

        if fullscreen_handler:
            self.postfullscreen(tag, idx)

        self.need_handle_fullscreen = True

        self.focus_driven_actions(tag)

    def focus_driven_actions(self, tag):
        """ Make some actions after focus """
        if self.conf(tag, "mpd_shut") == 1:
            Misc.send('vol mute', i3=self.i3ipc)

    def twin(self, tag: str, idx: int, with_subtag: bool = False):
        """ Detect target window.
            Args:
                tag (str): selected tag.
                idx (int): index in tag list.
                with_subtag (bool): contains subtag, special behaviour then.
        """
        if not with_subtag:
            return self.tagged[tag][idx]

        subtag_win_classes = self.subtag_info.get("class", {})
        for subidx, win in enumerate(self.tagged[tag]):
            if win.window_class in subtag_win_classes:
                return self.tagged[tag][subidx]

        return self.tagged[tag][0]

    def need_priority_check(self, tag):
        """ Checks that priority string is defined, then thecks that currrent
        window not in class set.

            Args:
                tag(str): target tag name

        """
        return "priority" in self.conf(tag) and \
            self.current_win.window_class not in set(self.conf(tag, "class"))

    def not_priority_win_class(self, tag, win):
        """ Window class is not priority class for the given tag

            Args:
                tag(str): target tag name
                win: window
        """
        return win.window_class in self.conf(tag, "class") and \
            win.window_class != self.conf(tag, "priority")

    def no_prioritized_wins(self, tag):
        """ Checks all tagged windows for the priority win.

            Args:
                tag(str): target tag name
        """
        return not [
            win for win in self.tagged[tag]
            if win.window_class == self.conf(tag, "priority")
        ]

    def go_next(self, tag: str) -> None:
        """ Circle over windows. Function "called" from the user-side.

        Args:
            tag (str): denotes target [tag]
        """
        self.sort_by_parent(tag)
        if not self.tagged[tag]:
            self.run_prog(tag)
        elif len(self.tagged[tag]) == 1:
            idx = 0
            self.focus_next(tag, idx, fullscreen_handler=False)
        else:
            idx = self.current_position[tag] % len(self.tagged[tag])
            if self.need_priority_check(tag):
                for win in self.tagged[tag]:
                    if self.no_prioritized_wins(tag):
                        self.run_prog(tag)
                        return
                for idx, win in enumerate(self.tagged[tag]):
                    if win.window_class == self.conf(tag, "priority"):
                        self.focus_next(tag, idx, inc_counter=False)
            elif self.current_win.id == self.twin(tag, idx).id:
                self.find_next_not_the_same_win(tag)
            else:
                self.focus_next(tag, idx)

    def go_subtag(self, tag: str, subtag: str) -> None:
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
            if not tagged_win_classes & subtagged_class_set:
                self.run_prog(tag, subtag)
            else:
                idx = 0
                self.focus_next(tag, idx, subtagged=True)

    def add_prop(self, tag_to_add: str, prop_str: str) -> None:
        """ Add property via [prop_str] to the target [tag].

        Args:
            tag (str): denotes the target tag.
            prop_str (str): string in i3-match format used to add/delete
                            target window in/from scratchpad.
        """
        if tag_to_add in self.cfg:
            self.add_props(tag_to_add, prop_str)

        for tag in self.cfg:
            if tag != tag_to_add:
                self.del_props(tag, prop_str)

        self.initialize(self.i3ipc)

    def del_prop(self, tag: str, prop_str: str) -> None:
        """ Delete property via [prop_str] to the target [tag].

            Args:
                tag (str): denotes the target tag.
                prop_str (str): string in i3-match format used to add/delete
                                target window in/from scratchpad.
        """
        self.del_props(tag, prop_str)

    def find_acceptable_windows(self, tag: str) -> None:
        """ Wrapper over Matcher.match to find acceptable windows and add it to
            tagged[tag] list.

            Args:
                tag (str): denotes the target tag.
        """
        for win in self.winlist:
            if self.match(win, tag):
                self.tagged.get(tag, {}).append(win)

    def tag_windows(self, invalidate_winlist=True) -> None:
        """ Find acceptable windows for the all tags and add it to the
            tagged[tag] list.

            Args:
                tag (str): denotes the target tag.
        """
        if invalidate_winlist:
            self.winlist = self.i3ipc.get_tree().leaves()
        self.tagged = {}

        for tag in self.cfg:
            self.tagged[tag] = []
            self.find_acceptable_windows(tag)

    def sort_by_parent(self, tag: str) -> None:
        """
            Sort windows by some infernal logic: At first sort by parent
            container order, than in any order.

            Args:
                tag (str): target tag to sort.
        """
        i = 0

        try:
            for tagged_win in self.tagged[tag]:
                for container_win in tagged_win.parent:
                    if container_win in self.tagged[tag]:
                        oldidx = self.tagged[tag].index(container_win)
                        self.tagged[tag].insert(
                            i, self.tagged[tag].pop(oldidx)
                        )
                        i += 1
        except TypeError:
            pass

    def add_wins(self, _, event) -> None:
        """ Tag window if it is match defined rules.

            Args:
                _: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        win = event.container
        for tag in self.cfg:
            if self.match(win, tag):
                self.tagged[tag].append(win)
        self.win = win

    def del_wins(self, _, event) -> None:
        """ Delete tag from window if it's closed.

            Args:
                _: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        win_con = event.container
        for tag in self.cfg:
            if self.match(win_con, tag):
                for win in self.tagged[tag]:
                    if win.id in self.restore_fullscreen:
                        self.restore_fullscreen.remove(win.id)

        for tag in self.cfg:
            for win in self.tagged[tag]:
                if win.id == win_con.id:
                    self.tagged[tag].remove(win)
        self.subtag_info = {}

    def set_curr_win(self, _, event) -> None:
        """ Cache the current window.

            Args:
                _: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        self.current_win = event.container

    def handle_fullscreen(self, _, event) -> None:
        """ Performs actions over the restore_fullscreen list.

            This function memorize the current state of the fullscreen property
            of windows for the future reuse it in functions which need to
            set/unset fullscreen state of the window correctly.

            Args:
                _: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        win = event.container
        self.fullscreened = self.i3ipc.get_tree().find_fullscreen()
        if self.need_handle_fullscreen:
            if win.fullscreen_mode:
                if win.id not in self.restore_fullscreen:
                    self.restore_fullscreen.append(win.id)
                    return
            if not win.fullscreen_mode:
                if win.id in self.restore_fullscreen:
                    self.restore_fullscreen.remove(win.id)
                    return
