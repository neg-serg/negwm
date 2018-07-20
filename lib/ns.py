""" Named scratchpad i3 module

This is a module about ion3/notion-like named scratchpad implementation.
You can think about it as floating "tabs" for windows, which can be
shown/hidden by request, with next "tab" navigation.

The foundation of it is a i3 mark function, you can create a mark with
tag+'-'+uuid format. And then this imformation used to performs all
actions.

Also I've hacked fullscreen behaviour for it, so you can always get
your scratchpad from fullscreen and also restore fullsreen state of the
window when needed.
"""

import subprocess
import uuid
from typing import Callable, List

import lib.geom as geom
from singleton import Singleton
from modi3cfg import modi3cfg
from main import Matcher, notify_msg, print_traceback


class ns(modi3cfg, Matcher):
    """ Named scratchpad class

    Parents:
        modi3cfg: configuration manager to autosave/autoload
                  TOML-configutation with inotify
        Matcher: class to check that window can be tagged with given tag by
                 WM_CLASS, WM_INSTANCE, regexes, etc

    Metaclass:
        Use Singleton metaclass from singleton module.

    """
    __metaclass__ = Singleton

    def __init__(self, i3, loop=None) -> None:
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

        self.i3.on('window::new', self.mark_tag)
        self.i3.on('window::close', self.unmark_tag)

    def initialize(self, i3):
        # winlist is used to reduce calling i3.get_tree() too many times.
        self.winlist = self.i3.get_tree()

        # fullscreen_list is used to perform fullscreen hacks
        self.fullscreen_list = []

        # nsgeom used to respect current screen resolution in the geometry
        # settings and scale it
        self.nsgeom = geom.geom(self.cfg)

        # marked used to get the list of current tagged windows
        # with the given tag
        self.marked = {l: [] for l in self.cfg}

        # i3ipc connection, bypassed by negi3mods runner
        self.i3 = i3

        # transients used to exclude dialogs and another another transient
        # windows from the usual named-scratchpad-geometry handling method
        self.transients = []

        # Mark all tags from the start
        self.mark_all_tags(hide=True)

        # Do not autosave geometry by default
        self.auto_save_geom(False)

        # focus_win_flag is a helper to perform attach/detach window to the
        # named scratchpad with add_prop/del_prop routines
        self.focus_win_flag = [False, ""]

    def make_mark_str(self, tag: str) -> str:
        """ Generate unique mark for the given [tag]

            Args:
                tag: tag string
        """
        return f'mark {tag}-{str(str(uuid.uuid4().fields[-1]))}'

    def focus(self, tag: str, hide=True) -> None:
        """ Show given [tag]

            Args:
                tag: tag string
                hide: optional predicate to hide all windows except current.
                      Should be used in the most cases because of better
                      performance and visual neatness
        """
        if not len(self.transients):
            [
                win.command('move container to workspace current')
                for win in self.marked[tag]
            ]
            if hide:
                self.unfocus_all_but_current(tag)
        else:
            try:
                self.transients[0].command('focus')
                del self.transients[0]
            except Exception:
                self.mark_all_tags(hide=False)

    def unfocus(self, tag: str) -> None:
        """ Hide given [tag]

            Args:
                tag: tag string
        """
        if self.geom_auto_save:
            self.geom_save(tag)
        [
            win.command('move scratchpad')
            for win in self.marked[tag]
        ]
        self.restore_fullscreens()

    def unfocus_all_but_current(self, tag: str) -> None:
        """ Hide all tagged windows except current.

            Args:
                tag: tag string
        """
        focused = self.i3.get_tree().find_focused()
        for win in self.marked[tag]:
            if win.id != focused.id:
                win.command('move scratchpad')
            else:
                win.command('move container to workspace current')

    def find_visible_windows(self, focused=None):
        """ Find windows visible on the screen now.

            Unfortunately for now external xprop application used for it,
            because of i3ipc gives no information about what windows
            shown/hidden or about _NET_WM_STATE_HIDDEN attributes

            Args:
                focused: denotes that [focused] window should be extracted from
                         i3.get_tree() or not
        """
        visible_windows = []
        wswins = []

        if focused is None:
            focused = self.i3.get_tree().find_focused()

        for win in focused.workspace().descendents():
            if win.window is not None:
                wswins.append(win)

        xprop = None
        for w in wswins:
            xprop = subprocess.run(
                ['xprop', '-id', str(w.window)],
                stdin=None,
                stdout=subprocess.PIPE
            ).stdout
            if xprop is not None:
                xprop = xprop.decode('UTF-8').strip()
                if xprop:
                    if '_NET_WM_STATE_HIDDEN' not in xprop:
                        visible_windows.append(w)

        return visible_windows

    def check_dialog_win(self, w):
        """ Check that window [w] is not dialog window

            Unfortunately for now external xprop application used for it,
            because of i3ipc gives no information about what windows dialog or
            not, shown/hidden or about _NET_WM_STATE_HIDDEN attribute or
            "custom" window attributes, etc.

            Args:
                w : target window to check
        """
        if w.window_instance == "Places" \
                or w.window_role == "GtkFileChooserDialog" \
                or w.window_class == "Dialog":
            return False
        ret = True
        xprop = None
        try:
            xprop = subprocess.run(
                ['xprop', '-id', str(w.window)],
                stdin=None,
                stdout=subprocess.PIPE
            ).stdout
        except Exception:
            print("get some problem in [check_dialog_win] in [nsd.py]")
            print_traceback()

        if xprop is not None:
            xprop = xprop.decode('UTF-8').strip()
            if xprop:
                if '_NET_WM_STATE_HIDDEN' not in xprop:
                    ret = not (
                        '_NET_WM_WINDOW_TYPE_DIALOG' in xprop
                        or
                        '_NET_WM_STATE_MODAL' in xprop
                    )
        return ret

    def dialog_toggle(self):
        """ Show dialog windows

            This function using self.check_dialog_win, which use information
            extracted from xprop application. And because of this it's not so
            fast. But this operation is pretty rare, so no problem here.
        """
        wlist = self.i3.get_tree().leaves()
        for win in wlist:
            if not self.check_dialog_win(win):
                win.command('move container to workspace current')

    def toggle_fs(self, win):
        """ Toggles fullscreen on/off and show/hide requested scratchpad after.

            Args:
                w : window that fullscreen state should be on/off.
        """
        if win.fullscreen_mode:
            win.command('fullscreen toggle')
            self.fullscreen_list.append(win)

    def toggle(self, tag: str) -> None:
        """ Toggle scratchpad with given [tag].

            Args:
                tag (str): denotes the target tag.
        """
        if not len(self.marked.get(tag, {})):
            prog_str = self.extract_prog_str(self.conf(tag))
            if prog_str:
                self.i3.command(f'exec {prog_str}')
            else:
                spawn_str = self.extract_prog_str(
                    self.conf(tag),
                    "spawn",
                    exe_file=False
                )
                if spawn_str:
                    self.i3.command(
                        f'exec ~/.config/i3/send executor run {spawn_str}'
                    )

        if self.visible_count_on_tag(tag) > 0:
            self.unfocus(tag)
            return

        # We need to hide scratchpad it is visible,
        # regardless it focused or not
        focused = self.i3.get_tree().find_focused()

        for w in self.marked[tag]:
            if focused.id == w.id:
                self.unfocus(tag)
                return

        if len(self.marked.get(tag, {})):
            self.toggle_fs(focused)
            self.focus(tag)

    def focus_sub_tag(self, tag: str, subtag_classes_set):
        """ Cycle over the subtag windows.

            Args:
                tag (str): denotes the target tag.
                subtag_classes_set (set): subset of classes of target [tag]
                                          which distinguish one subtag from
                                          another.
        """
        focused = self.i3.get_tree().find_focused()

        self.toggle_fs(focused)

        if focused.window_class in subtag_classes_set:
            return

        self.focus(tag)

        visible_windows = self.find_visible_windows(focused)
        for w in visible_windows:
            for i in self.marked[tag]:
                if w.window_class in subtag_classes_set and w.id == i.id:
                    self.i3.command(f'[con_id={w.id}] focus')

        for _ in self.marked[tag]:
            focused = self.i3.get_tree().find_focused()
            if focused.window_class not in subtag_classes_set:
                self.next_win()

    def run_subtag(self, tag: str, subtag: str) -> None:
        """ Run-or-focus the application for subtag

            Args:
                tag (str): denotes the target tag.
                subtag (str): denotes the target subtag.
        """
        if subtag in self.conf(tag, "subtag"):
            class_list = [win.window_class for win in self.marked[tag]]
            subtag_classes_set = self.conf(tag, "subtag", subtag, "class")
            subtag_classes_matched = [
                w for w in class_list if w in subtag_classes_set
            ]
            if not len(subtag_classes_matched):
                try:
                    prog_str = self.extract_prog_str(
                        self.conf(tag, "subtag", subtag)
                    )
                    self.i3.command(f'exec {prog_str}')
                    self.focus_win_flag = [True, tag]
                except Exception:
                    print_traceback()
            else:
                self.focus_sub_tag(tag, subtag_classes_set)
        else:
            self.toggle(tag)

    def restore_fullscreens(self) -> None:
        """ Restore all fullscreen windows
        """
        [win.command('fullscreen toggle') for win in self.fullscreen_list]
        self.fullscreen_list = []

    def visible_count_on_tag(self, tag: str):
        """ Counts visible windows for given tag

            Args:
                tag (str): denotes the target tag.
        """
        visible_windows = self.find_visible_windows()
        vmarked = 0
        for w in visible_windows:
            for i in self.marked[tag]:
                vmarked += (w.id == i.id)
        return vmarked

    def get_current_tag(self, focused) -> str:
        """ Get the current tag

            This function use focused window to determine the current tag.

            Args:
                focused : focused window.
        """
        for tag in self.cfg:
            for i in self.marked[tag]:
                if focused.id == i.id:
                    return tag

    def apply_to_current_tag(self, func: Callable) -> bool:
        """ Apply function [func] to the current tag

            This is the generic function used in next_win, hide_current
            and another to perform actions on the currently selected tag.

            Args:
                func(Callable) : function to apply.
        """
        curr_tag = self.get_current_tag(self.i3.get_tree().find_focused())
        curr_tag_exits = (curr_tag is not None)
        if curr_tag_exits:
            func(curr_tag)
        return curr_tag_exits

    def next_win(self, hide=True) -> None:
        """ Show the next window for the currently selected tag.

            Args:
                hide(bool) : hide another windows for the current tag or not.
        """
        def next_win_(tag: str) -> None:
            self.focus(tag, Hide)
            for idx, win in enumerate(self.marked[tag]):
                if focused_win.id != win.id:
                    self.marked[tag][idx].command(
                        'move container to workspace current'
                    )
                    self.marked[tag].insert(
                        len(self.marked[tag]),
                        self.marked[tag].pop(idx)
                    )
                    win.command('move scratchpad')
            self.focus(tag, Hide)
        Hide = hide
        focused_win = self.i3.get_tree().find_focused()
        self.apply_to_current_tag(next_win_)

    def hide_current(self) -> None:
        """ Hide the currently selected tag.
        """
        if not self.apply_to_current_tag(self.unfocus):
            self.i3.command('[con_id=__focused__] scratchpad show')

    def geom_restore(self, tag: str) -> None:
        """ Show the next window for the current selected tag.

            Args:
                tag(str) : hide another windows for the current tag or not.
        """
        for idx, win in enumerate(self.marked[tag]):
            # delete previous mark
            del self.marked[tag][idx]

            # then make a new mark and move scratchpad
            win_cmd = f"{self.make_mark_str(tag)}, \
                move scratchpad, {self.nsgeom.get_geom(tag)}"
            win.command(win_cmd)
            self.marked[tag].append(win)

    def geom_restore_current(self) -> None:
        """ Restore geometry for the current selected tag.
        """
        self.apply_to_current_tag(self.geom_restore)

    def geom_dump(self, tag: str) -> None:
        """ Dump geometry for the given tag

            Args:
                tag(str) : denotes target tag.
        """
        focused = self.i3.get_tree().find_focused()
        for idx, win in enumerate(self.marked[tag]):
            if win.id == focused.id:
                self.cfg[tag]["geom"] = f"{focused.rect.width}x\
                    {focused.rect.height}+{focused.rect.x}+{focused.rect.y}"
                self.dump_config()
                break

    def geom_save(self, tag: str) -> None:
        """ Save geometry for the given tag

            Args:
                tag(str) : denotes target tag.
        """
        focused = self.i3.get_tree().find_focused()
        for idx, win in enumerate(self.marked[tag]):
            if win.id == focused.id:
                self.cfg[tag]["geom"] = f"{focused.rect.width}x\
                    {focused.rect.height}+{focused.rect.x}+{focused.rect.y}"
                if win.rect.x != focused.rect.x \
                    or win.rect.y != focused.rect.y \
                    or win.rect.width != focused.rect.width \
                        or win.rect.height != focused.rect.height:
                    self.nsgeom = geom.geom(self.cfg)
                    win.rect.x = focused.rect.x
                    win.rect.y = focused.rect.y
                    win.rect.width = focused.rect.width
                    win.rect.height = focused.rect.height
                break

    def auto_save_geom(self, save=True, with_notification=False):
        """ Set geometry autosave option with optional notification.

            Args:
                save(bool): predicate that shows that want to enable/disable
                             autosave mode.
                with_notification(bool): to create notify-osd-based
                                         notification or not.
        """
        self.geom_auto_save = save
        if with_notification:
            notify_msg(f"geometry autosave={save}")

    def autosave_toggle(self):
        """ Toggle autosave mode.
        """
        if self.geom_auto_save:
            self.auto_save_geom(False, with_notification=True)
        else:
            self.auto_save_geom(True, with_notification=True)

    def geom_dump_current(self):
        """ Dump geometry for the current selected tag.
        """
        self.apply_to_current_tag(self.geom_dump)

    def geom_save_current(self):
        """ Save geometry for the current selected tag.
        """
        self.apply_to_current_tag(self.geom_save)

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
                if self.marked[t] != []:
                    for win in self.marked[t]:
                        win.command('unmark')

        self.initialize(self.i3)

    def del_prop(self, tag, prop_str):
        """ Delete property via [prop_str] to the target [tag].

            Args:
                tag (str): denotes the target tag.
                prop_str (str): string in i3-match format used to add/delete
                                target window in/from scratchpad.
        """
        self.del_props(tag, prop_str)

    def switch(self, args: List) -> None:
        """ Defines pipe-based IPC for nsd module. With appropriate function
            bindings.

            This function defines bindings to the named_scratchpad methods that
            can be used by external users as i3-bindings, sxhkd, etc. Need the
            [send] binary which can send commands to the appropriate FIFO.

            Args:
                args (List): argument list for the selected function.
        """
        {
            "show": self.focus,
            "hide": self.unfocus_all_but_current,
            "next": self.next_win,
            "toggle": self.toggle,
            "hide_current": self.hide_current,
            "geom_restore": self.geom_restore_current,
            "geom_dump": self.geom_dump_current,
            "geom_save": self.geom_save_current,
            "geom_autosave_mode": self.autosave_toggle,
            "subtag": self.run_subtag,
            "add_prop": self.add_prop,
            "del_prop": self.del_prop,
            "reload": self.reload_config,
            "dialog": self.dialog_toggle,
        }[args[0]](*args[1:])

    def check_win_marked(self, win, tag):
        """ Delete property via [prop_str] to the target [tag].

            This function used for add_prop/delete_prop methods to not make the
            same actions twice. We use [tag] as prefix to the unique mark name.

            Args:
                win: this windows will be checked for mark on/off.
                tag (str): tag, which used as prefix to the mark name.
        """
        for mrk in win.marks:
            if tag + "-" in mrk:
                return True
        return False

    def mark(self, tag, hide=True):
        """ Add unique mark to the target [tag] with optional [hide].

            Args:
                tag (str): denotes the target tag.
                hide (bool): hide window or not. Primarly used to cleanup
                             "garbage" that can appear after i3 (re)start, etc.
                             Because of I've think that is't better to make
                             screen clear after (re)start.
        """
        leaves = self.i3.get_tree().leaves()
        for win in leaves:
            if self.match(win, tag):
                if not self.check_win_marked(win, tag):
                    # scratch move
                    hide_cmd = ''
                    if hide:
                        hide_cmd = '[con_id=__focused__] scratchpad show'
                    win_cmd = f"{self.make_mark_str(tag)}, move scratchpad, \
                        {self.nsgeom.get_geom(tag)}, {hide_cmd}"
                    win.command(win_cmd)
                    self.marked[tag].append(win)
        self.winlist = self.i3.get_tree()
        self.dialog_toggle()

    def mark_tag(self, i3, event) -> None:
        """ Add unique mark to the new window.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        win = event.container
        self.winlist = self.i3.get_tree()
        for tag in self.cfg:
            if self.match(win, tag):
                if self.check_dialog_win(win):
                    # scratch_move
                    win_cmd = f"{self.make_mark_str(tag)}, move scratchpad, \
                        {self.nsgeom.get_geom(tag)}"
                    win.command(win_cmd)
                    self.marked[tag].append(win)
                else:
                    self.transients.append(win)
        self.dialog_toggle()
        self.winlist = self.i3.get_tree()

        # Special hack to invalidate windows after subtag start
        if self.focus_win_flag[0]:
            special_tag = self.focus_win_flag[1]
            if special_tag in self.cfg:
                self.focus(special_tag, hide=True)
            self.focus_win_flag[0] = False
            self.focus_win_flag[1] = ""

    def unmark_tag(self, i3, event) -> None:
        """ Delete unique mark from the closed window.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        win_ev = event.container
        self.winlist = self.i3.get_tree()
        for tag in self.cfg:
            for _, win in enumerate(self.marked[tag]):
                if win.id == win_ev.id:
                    del self.marked[tag][_]
                    self.focus(tag)
                    for tr in self.transients:
                        if tr.id == win.id:
                            self.transients.remove(tr)
                    break
        self.winlist = self.i3.get_tree()

    def mark_all_tags(self, hide: bool = True) -> None:
        """ Add marks to the all tags.

            Args:
                hide (bool): hide window or not. Primarly used to cleanup
                             "garbage" that can appear after i3 (re)start, etc.
                             Because of I've think that is't better to make
                             screen clear after (re)start.
        """
        self.winlist = self.i3.get_tree()
        leaves = self.winlist.leaves()
        for tag in self.cfg:
            for win in leaves:
                if self.match(win, tag):
                    if self.check_dialog_win(win):
                        # scratch move
                        hide_cmd = ''
                        if hide:
                            hide_cmd = '[con_id=__focused__] scratchpad show'
                        win_cmd = f"{self.make_mark_str(tag)}, \
                            move scratchpad, \
                            {self.nsgeom.get_geom(tag)}, {hide_cmd}"
                        win.command(win_cmd)
                        self.marked[tag].append(win)
                    else:
                        self.transients.append(win)
        self.winlist = self.i3.get_tree()
        self.dialog_toggle()

