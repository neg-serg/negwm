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

import uuid
from typing import List, Callable, Set
from . import geom
from . cfg import cfg
from . matcher import Matcher
from . misc import Misc
from . negewmh import NegEWMH
from . extension import extension

class scratchpad(extension, cfg, Matcher):
    """ Named scratchpad class
        cfg: configuration manager to autosave/autoload
             TOML-configutation with inotify
        Matcher: class to check that window can be tagged with given tag by
                 WM_CLASS, WM_INSTANCE, regexes, etc
    """

    def __init__(self, i3) -> None:
        """ Init function
            i3: i3ipc connection """
        # Initialize superclasses.
        super().__init__()
        cfg.__init__(self, i3)
        Matcher.__init__(self)
        self.win = None # reducing  calling i3.get_tree() too many times.
        self.fullscreen_list = [] # performing fullscreen hacks
        # nsgeom used to respect current screen resolution in the geometry
        # settings and scale it
        self.nsgeom = geom.geom(self.cfg)
        # marked used to get the list of current tagged windows
        # with the given tag
        self.marked = {l: [] for l in self.cfg}
        self.mark_all_tags(hide=True) # Mark all tags from the start
        self.auto_save_geom(False) # Do not autosave geometry by default
        # focus_win_flag is a helper to perform attach/detach window to the
        # named scratchpad with add_prop/del_prop routines
        self.focus_win_flag = [False, ""]
        self.i3ipc = i3 # i3ipc connection, bypassed by negi3wm runner
        self.bindings = {
            "show": self.show_scratchpad,
            "hide": self.hide_scratchpad_all_but_current,
            "next": self.next_win_on_curr_tag,
            "toggle": self.toggle,
            "hide_current": self.hide_current,
            "geom_restore": self.geom_restore_current,
            "geom_dump": self.geom_dump_current,
            "geom_save": self.geom_save_current,
            "geom_autosave": self.autosave_toggle,
            "subtag": self.run_subtag,
            "add_prop": self.add_prop,
            "del_prop": self.del_prop,
            "reload": self.reload_config,
            "dialog": self.dialog_toggle,
        }
        i3.on('window::new', self.mark_tag)
        i3.on('window::close', self.unmark_tag)

    def taglist(self) -> List:
        """ Returns list of tags without transients windows. """
        tag_list = list(self.cfg.keys())
        tag_list.remove('transients')
        return tag_list

    @staticmethod
    def mark_uuid_tag(tag: str) -> str:
        """ Generate unique mark for the given [tag]
            tag: tag string """
        return f'mark {tag}-{str(str(uuid.uuid4().fields[-1]))}'

    def show_scratchpad(self, tag: str, hide: bool = True) -> None:
        """ Show given [tag]
            tag: tag string
            hide: optional predicate to hide all windows except current. Should
            be used in the most cases because of better performance and visual
            neatness """
        win_to_focus = None
        for win in self.marked[tag]:
            win.command('move window to workspace current')
            win_to_focus = win
        if hide and tag != 'transients':
            self.hide_scratchpad_all_but_current(tag, win_to_focus)
        if win_to_focus is not None:
            win_to_focus.command('focus')

    def hide_scratchpad(self, tag: str) -> None:
        """ Hide given [tag]
            tag (str): scratchpad name to hide """
        if self.geom_auto_save:
            self.geom_save(tag)
        for win in self.marked[tag]:
            win.command('move scratchpad')
        self.restore_fullscreens()

    def hide_scratchpad_all_but_current(self, tag: str, current_win) -> None:
        """ Hide all tagged windows except current.
            tag: tag string """
        if len(self.marked[tag]) > 1 and current_win is not None:
            for win in self.marked[tag]:
                if win.id != current_win.id:
                    win.command('move scratchpad')
                else:
                    win.command('move window to workspace current')

    def find_visible_windows(self) -> List:
        """ Find windows on the current workspace, which is enough for
        scratchpads.
        focused: denotes that [focused] window should be extracted from
        i3.get_tree() or not """
        focused = self.i3ipc.get_tree().find_focused()
        return NegEWMH.find_visible_windows(
            focused.workspace().leaves()
        )

    def dialog_toggle(self) -> None:
        """ Show dialog windows """
        self.show_scratchpad('transients', hide=False)

    def toggle_fs(self, win) -> None:
        """ Toggles fullscreen on/off and show/hide requested scratchpad after.
            w: window that fullscreen state should be on/off. """
        if win.fullscreen_mode:
            win.command('fullscreen toggle')
            self.fullscreen_list.append(win)

    def toggle(self, tag: str) -> None:
        """ Toggle scratchpad with given [tag].
            tag (str): denotes the target tag. """
        if not self.marked.get(tag, []):
            prog_str = self.extract_prog_str(self.conf(tag))
            if prog_str:
                self.i3ipc.command(f'exec {prog_str}')
            else:
                spawn_str = self.extract_prog_str(
                    self.conf(tag), "spawn", exe_file=False
                )
                if spawn_str:
                    executor = extension.get_mods().get('executor')
                    if executor is not None:
                        executor.bindings['run'](spawn_str)
        if self.visible_window_with_tag(tag):
            self.hide_scratchpad(tag)
            return
        # We need to hide scratchpad it is visible,
        # regardless it focused or not
        focused = self.i3ipc.get_tree().find_focused()
        if self.marked.get(tag, []):
            self.toggle_fs(focused)
            self.show_scratchpad(tag)

    def focus_sub_tag(self, tag: str, subtag_classes_set: Set) -> None:
        """ Cycle over the subtag windows.
            tag (str): denotes the target tag.
            subtag_classes_set (set): subset of classes of target [tag] which
            distinguish one subtag from another. """
        focused = self.i3ipc.get_tree().find_focused()
        self.toggle_fs(focused)
        if focused.window_class in subtag_classes_set:
            return
        self.show_scratchpad(tag)
        for _ in self.marked[tag]:
            if focused.window_class not in subtag_classes_set:
                self.next_win_on_curr_tag()
                focused = self.i3ipc.get_tree().find_focused()

    def run_subtag(self, tag: str, subtag: str) -> None:
        """ Run-or-focus the application for subtag
            tag (str): denotes the target tag.
            subtag (str): denotes the target subtag. """
        if subtag in self.conf(tag):
            class_list = [win.window_class for win in self.marked[tag]]
            subtag_classes_set = self.conf(tag, subtag, "class")
            subtag_classes_matched = [
                w for w in class_list if w in subtag_classes_set
            ]
            if not subtag_classes_matched:
                prog_str = self.extract_prog_str(self.conf(tag, subtag))
                self.i3ipc.command(f'exec {prog_str}')
                self.focus_win_flag = [True, tag]
            else:
                self.focus_sub_tag(tag, subtag_classes_set)
        else:
            self.toggle(tag)

    def restore_fullscreens(self) -> None:
        """ Restore all fullscreen windows """
        for win in self.fullscreen_list:
            win.command('fullscreen toggle')
        self.fullscreen_list = []

    def visible_window_with_tag(self, tag: str) -> bool:
        """ Counts visible windows for given tag
            tag (str): denotes the target tag. """
        for win in self.find_visible_windows():
            for i in self.marked[tag]:
                if win.id == i.id:
                    return True
        return False

    def get_current_tag(self, focused) -> str:
        """ Get the current tag This function use focused window to determine
        the current tag.
        focused : focused window. """
        for tag in self.cfg:
            for i in self.marked[tag]:
                if focused.id == i.id:
                    return tag

        return ''

    def apply_to_current_tag(self, func: Callable) -> bool:
        """ Apply function [func] to the current tag
            This is the generic function used in next_win_on_curr_tag,
            hide_current and another to perform actions on the currently
            selected tag.
            func(Callable) : function to apply. """
        curr_tag = self.get_current_tag(self.i3ipc.get_tree().find_focused())
        if curr_tag:
            func(curr_tag)
        return bool(curr_tag)

    def next_win_on_curr_tag(self, hide: bool = True) -> None:
        """ Show the next window for the currently selected tag.
            hide (bool): hide window or not. Primarly used to cleanup "garbage"
            that can appear after i3 (re)start, etc. Because of I've think that
            is't better to make screen clear after (re)start. """
        def next_win(tag: str) -> None:
            self.show_scratchpad(tag, hide_)
            for idx, win in enumerate(self.marked[tag]):
                if focused_win.id != win.id:
                    self.marked[tag][idx].command(
                        'move window to workspace current'
                    )
                    self.marked[tag].insert(
                        len(self.marked[tag]),
                        self.marked[tag].pop(idx)
                    )
                    win.command('move scratchpad')
            self.show_scratchpad(tag, hide_)

        hide_ = hide
        focused_win = self.i3ipc.get_tree().find_focused()
        self.apply_to_current_tag(next_win)

    def hide_current(self) -> None:
        """ Hide the currently selected tag. """
        self.apply_to_current_tag(self.hide_scratchpad)

    def geom_restore(self, tag: str) -> None:
        """ Restore default window geometry
        tag(str) : hide another windows for the current tag or not. """
        for idx, win in enumerate(self.marked[tag]):
            # delete previous mark
            del self.marked[tag][idx]
            # then make a new mark and move scratchpad
            win_cmd = f"{scratchpad.mark_uuid_tag(tag)}, \
                move scratchpad, {self.nsgeom.get_geom(tag)}"
            win.command(win_cmd)
            self.marked[tag].append(win)

    def geom_restore_current(self) -> None:
        """ Restore geometry for the current selected tag. """
        self.apply_to_current_tag(self.geom_restore)

    def geom_dump(self, tag: str) -> None:
        """ Dump geometry for the given tag
            tag(str): denotes target tag. """
        focused = self.i3ipc.get_tree().find_focused()
        for win in self.marked[tag]:
            if win.id == focused.id:
                focused_geom = f"{focused.rect.width}x{focused.rect.height}" \
                    f"+{focused.rect.x}+{focused.rect.y}"
                self.cfg[tag]["geom"] = focused_geom
                self.dump_config()
                break

    def geom_save(self, tag: str) -> None:
        """ Save geometry for the given tag
            tag(str): denotes target tag. """
        focused = self.i3ipc.get_tree().find_focused()
        for win in self.marked[tag]:
            if win.id == focused.id:
                focused_geom = f"{focused.rect.width}x{focused.rect.height}" \
                    f"+{focused.rect.x}+{focused.rect.y}"
                self.cfg[tag]["geom"] = focused_geom
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

    def auto_save_geom(self, save: bool = True,
                       with_notification: bool = False) -> None:
        """ Set geometry autosave option with optional notification.
            save(bool): predicate that shows that want to enable/disable
            autosave mode.
            with_notification(bool): to create notify-osd-based notification or
            not. """
        self.geom_auto_save = save
        if with_notification:
            Misc.notify_msg(f"geometry autosave={save}")

    def autosave_toggle(self) -> None:
        """ Toggle autosave mode. """
        if self.geom_auto_save:
            self.auto_save_geom(False, with_notification=True)
        else:
            self.auto_save_geom(True, with_notification=True)

    def geom_dump_current(self) -> None:
        """ Dump geometry for the current selected tag. """
        self.apply_to_current_tag(self.geom_dump)

    def geom_save_current(self) -> None:
        """ Save geometry for the current selected tag. """
        self.apply_to_current_tag(self.geom_save)

    def add_prop(self, tag_to_add: str, prop_str: str) -> None:
        """ Add property via [prop_str] to the target [tag].
            tag_to_add (str): denotes the target tag.
            prop_str (str): string in i3-match format used to add/delete target
            window in/from scratchpad. """
        if tag_to_add in self.cfg:
            self.add_props(tag_to_add, prop_str)
        for tag in self.cfg:
            if tag != tag_to_add:
                self.del_props(tag, prop_str)
                if self.marked[tag] != []:
                    for win in self.marked[tag]:
                        win.command('unmark')
        self.__init__(self.i3ipc)

    def del_prop(self, tag: str, prop_str: str) -> None:
        """ Delete property via [prop_str] to the target [tag].
            tag (str): denotes the target tag.
            prop_str (str): string in i3-match format used to add/delete target
            window in/from scratchpad.
        """
        self.del_props(tag, prop_str)

    def mark_tag(self, _, event) -> None:
        """ Add unique mark to the new window.
            _: i3ipc connection.
            event: i3ipc event. We can extract window from it using
            event.container. """
        win = event.container
        is_dialog_win = NegEWMH.is_dialog_win(win)

        self.win = win
        for tag in self.cfg:
            if not is_dialog_win and tag != "transients":
                if self.match(win, tag):
                    # scratch_move
                    win.command(
                        f"{scratchpad.mark_uuid_tag(tag)}, move scratchpad, \
                        {self.nsgeom.get_geom(tag)}")
                    self.marked[tag].append(win)
                    self.show_scratchpad(tag, hide=True)
            elif is_dialog_win and tag == "transients":
                win.command(
                    f"{scratchpad.mark_uuid_tag('transients')}, \
                    move scratchpad")
                self.marked["transients"].append(win)

        # Special hack to invalidate windows after subtag start
        if self.focus_win_flag[0]:
            special_tag = self.focus_win_flag[1]
            if special_tag in self.cfg:
                self.show_scratchpad(special_tag, hide=True)
            self.focus_win_flag[0] = False
            self.focus_win_flag[1] = ""

        self.dialog_toggle()

    def unmark_tag(self, _, event) -> None:
        """ Delete unique mark from the closed window.
            _: i3ipc connection.
            event: i3ipc event. We can extract window from it using
            event.container """
        win_ev = event.container
        self.win = win_ev
        for tag in self.taglist():
            for win in self.marked[tag]:
                if win.id == win_ev.id:
                    self.marked[tag].remove(win)
                    self.show_scratchpad(tag)
                    break
        if win_ev.fullscreen_mode:
            self.apply_to_current_tag(self.hide_scratchpad)
        for transient in self.marked["transients"]:
            if transient.id == win_ev.id:
                self.marked["transients"].remove(transient)

    def mark_all_tags(self, hide: bool = True) -> None:
        """ Add marks to the all tags.
            hide (bool): hide window or not. Primarly used to cleanup "garbage"
            that can appear after i3 (re)start, etc. Because of I've think that
            is't better to make screen clear after (re)start. """
        winlist = self.i3ipc.get_tree().leaves()
        hide_cmd = ''
        for win in winlist:
            is_dialog_win = NegEWMH.is_dialog_win(win)
            for tag in self.cfg:
                if not is_dialog_win and tag != "transients":
                    if self.match(win, tag):
                        if hide:
                            hide_cmd = '[con_id=__focused__] scratchpad show'
                        win_cmd = f"{scratchpad.mark_uuid_tag(tag)}, \
                            move scratchpad, \
                            {self.nsgeom.get_geom(tag)}, {hide_cmd}"
                        win.command(win_cmd)
                        self.marked[tag].append(win)
                if is_dialog_win:
                    win_cmd = f"{scratchpad.mark_uuid_tag('transients')}, \
                        move scratchpad"
                    win.command(win_cmd)
                    self.marked["transients"].append(win)
            self.win = win
