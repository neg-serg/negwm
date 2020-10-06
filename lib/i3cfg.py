#!/usr/bin/python3

import os
from typing import List

from . misc import Misc
from . cfg import cfg
from . extension import extension
from . checker import checker

class i3cfg(extension, cfg):
    def __init__(self, i3) -> None:
        super().__init__()
        cfg.__init__(self, i3)
        self.i3ipc = i3
        self.bindings = {
            "print": self.print,
            "dump": self.dump_cfg,
            "reload": self.reload_config,
        }
        self.send_path = '${XDG_CONFIG_HOME}/i3/bin/send'

    def print(self) -> None:
        print(''.join(self.generate()))

    def dump_cfg(self) -> None:
        i3_cfg, test_cfg = 'config', '.config'
        generated_cfg = '\n'.join(self.generate())
        with open(Misc.i3path() + test_cfg, 'w', encoding='utf8') as fp:
            fp.write(generated_cfg)
        if checker.check_i3_config(verbose=False, cfg=test_cfg):
            with open(Misc.i3path() + i3_cfg, 'w', encoding='utf8') as fp:
                fp.write(generated_cfg)
            os.remove(Misc.i3path() + test_cfg)

    def generate(self):
        ret = []
        cfg_sections = self.cfg.get('sections', [])
        if cfg_sections:
            for section in cfg_sections:
                section_data = getattr(self, section)()
                ret.append(section_data)
        bind_modes = self.cfg.get('bind_modes', [])
        for keybind in bind_modes:
            bind_name, mode_bind = keybind[0], keybind[1]
            keybind_data = getattr(self, 'mode_' + bind_name)(
                mode_name=bind_name, mode_bind=mode_bind
            )
            ret.append(keybind_data)
        return ret

    def autostart(self) -> str:
        return '\n'.join(self.cfg.get('autostart', [])) + '\n'

    def gaps(self) -> str:
        return '\n'.join(self.cfg.get('gaps', [])) + '\n'

    def general(self) -> str:
        return '\n'.join(self.cfg.get('general', [])) + '\n'

    def focus_settings(self) -> str:
        return '\n'.join(self.cfg.get('focus_settings', [])) + '\n'

    def theme(self) -> str:
        return '\n'.join(self.cfg.get('theme', [])) + '\n'

    def color_theme(self) -> str:
        return '\n'.join(self.cfg.get('color_theme', [])) + '\n'

    @staticmethod
    def scratchpad_bindings(mode) -> str:
        ret = ''
        def get_binds(mode, tag, settings, p, subtag='') -> str:
            ret = ''
            pref, postfix = '', ''
            if mode != 'default':
                pref, postfix = '\t', ',$exit'
            get_binds = p.split('_')
            mode_ = get_binds[1]
            cmd = get_binds[2]
            if len(get_binds) == 3:
                if mode_ == mode:
                    for keybind in settings[p]:
                        ret += f'{pref.strip()}bindsym {keybind.strip()}' \
                            f' $scratchpad {cmd.strip()} {tag.strip()} ' \
                            f'{subtag.strip()} {postfix.strip()}\n'
            return ret

        scratchpad = extension.get_mods()['scratchpad']
        for tag,settings in scratchpad.cfg.items():
            for param in settings:
                if isinstance(settings[param], dict):
                    for p in settings[param]:
                        if p.startswith('keybind_'):
                            subtag = param
                            ret += get_binds(
                                mode, tag, settings[param], p, subtag=subtag
                            )
                elif param.startswith('keybind_'):
                    ret += get_binds(mode, tag, settings, param)
        return ret

    @staticmethod
    def circle_bindings(mode) -> str:
        ret = ''
        def get_binds(mode, tag, settings, p, subtag='') -> str:
            ret = ''
            pref, postfix = '', ''
            if mode != 'default':
                pref, postfix = '\t', ',$exit'
            get_binds = p.split('_')
            mode_ = get_binds[1]
            cmd = get_binds[2]
            if len(get_binds) == 3:
                if mode_ == mode:
                    subtag += ' '
                    for keybind in settings[p]:
                        ret += f'{pref}bindsym {keybind} $circle' \
                            f' {cmd} {tag} {subtag}{postfix}\n'
            return ret

        circle = extension.get_mods()['circle']
        for tag, settings in circle.cfg.items():
            for param in settings:
                if isinstance(settings[param], dict):
                    for p in settings[param]:
                        if p.startswith('keybind_'):
                            subtag = param
                            ret += get_binds(
                                mode, tag, settings[subtag], p, subtag
                            )
                elif param.startswith('keybind_'):
                    ret += get_binds(mode, tag, settings, param)
        return ret

    def mods_commands(self) -> str:
        ret = ''
        for mod in sorted(extension.get_mods()):
            ret += (f'set ${mod} exec --no-startup-id {self.send_path} {mod}\n')
        return ret

    def workspaces(self) -> str:
        ret = ''
        for index, ws in enumerate(self.cfg['ws_list']):
            ret += f'set ${ws.split(":")[1]} "{index + 1} :: {ws}"\n'
        return ret

    @staticmethod
    def scratchpad_hide_cmd(hide: bool) -> str:
        """ Returns cmd needed to hide scratchpad. """
        if hide:
            return ", [con_id=__focused__] scratchpad show"
        return ""

    def rules(self) -> str:
        def fill_rules_dict(mod, cmd_dict) -> List:
            config = mod.cfg
            for tag in config:
                cmd_dict[tag] = []
                for attr in config[tag]:
                    for fill in ['class', 'instance', 'name', 'role']:
                        cmd_dict[tag].append(info(config, tag, attr, fill))
            return cmd_dict

        def rules_mod(modname):
            """ Create i3 match rules for all tags. """
            ret = ''
            mod = extension.get_mods().get(modname, None)
            if mod is None:
                return ''
            cmd_dict = fill_rules_dict(mod, {})
            for tag in cmd_dict:
                rules = list(filter(lambda str: str != '', cmd_dict[tag]))
                if rules:
                    ret += f'set ${modname}-{tag} [' + ' '.join(rules) + ']'
                    ret += '\n'
            return (ret, cmd_dict, mod)

        def rules_scratchpad() -> str:
            """ Create i3 match rules for all tags. """
            (ret, cmd_dict, scratchpad) = rules_mod('scratchpad')
            ret += '\n'
            for tag in cmd_dict:
                if tag in {'transients'}:
                    geom = scratchpad.nsgeom.get_geom(tag)
                    ret += f'for_window $scratchpad-{tag} move scratchpad, {geom}\n'
                else:
                    ret += f'for_window $scratchpad-{tag} floating enable\n'
            return ret

        def rules_circle() -> str:
            (ret, _, circle) = rules_mod('circle')
            for tag in circle.cfg:
                focus_cmd = ''
                ws = circle.cfg[tag].get('ws', '')
                focus = bool(circle.cfg[tag].get('focus', True))
                if focus:
                    focus_cmd = ',focus'
                if ws:
                    ret += f'for_window $circle-{tag}' \
                        f' move workspace ${ws}{focus_cmd}\n'
            return ret

        def info(config: dict, tag: str, attr: str, fill: str) -> str:
            """ Create rule in i3 commands format
                Args:
                    config (dict): extension config.
                    tag (str): target tag.
                    attr (str): tag attrubutes.
                    fill (str): attribute to fill.
            """
            conv_dict_attr = {
                'class': 'class',
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

        def plain_rules() -> str:
            rules = self.cfg.get('plain_rules', [])
            if rules:
                return ''.join(map(lambda s: 'for_window ' + s + '\n', rules))
            return ''
        return rules_scratchpad() + \
            rules_circle() + \
            plain_rules()

    @staticmethod
    def mode_start(name) -> str:
        return 'mode ' + name + ' {\n'

    @staticmethod
    def mode_end() -> str:
        ret = ''
        bindings = ['Return', 'Escape', 'space', 'Control+C', 'Control+G']
        for keybind in bindings:
            ret += f'bindsym {keybind},$exit\n'
        return ret + '}\n'

    @staticmethod
    def mode_binding(keymap, name) -> str:
        return f'bindsym {keymap} mode "{name}"\n'

    def bind(self, section_name, post, end, pre='bindsym') -> str:
        ret = ''
        section = self.cfg.get(section_name, {})
        if section:
            binds = section.get('binds', [])
            funcs = section.get('funcs')
            modkey = section.get('modkey', '')
            params = section.get('params', [])
            if modkey:
                modkey += '+'
            if binds and funcs:
                ret += '\n'
                param_str = ' '.join(params).strip()
                for bind in binds:
                    for i, key in enumerate(bind):
                        ret += f'{pre} {modkey}{key} {post} ' \
                            f'{funcs[i]}{param_str}{end}\n'
                ret += '\n'
        return ret

    def mode_resize(self, mode_name, mode_bind) -> str:
        return i3cfg.mode_binding(mode_bind, mode_name) + \
            i3cfg.mode_start(mode_name) + \
            self.bind('resize_plus', '$win_action resize', '') + \
            self.bind('resize_minus', '$win_action resize', '') + \
            i3cfg.mode_end()

    def mode_spec(self, mode_name, mode_bind) -> str:
        def menu_spec() -> str:
            return self.bind('menu_spec', '$menu', ',$exit')

        def misc_spec() -> str:
            return self.bind('misc_spec', '', ',$exit')

        return i3cfg.mode_binding(mode_bind, mode_name) + \
            i3cfg.mode_start(mode_name) + \
            misc_spec() + \
            menu_spec() + \
            i3cfg.scratchpad_bindings(mode_name) + \
            i3cfg.circle_bindings(mode_name) + \
            i3cfg.mode_end()

    def mode_wm(self, mode_name, mode_bind) -> str:
        def split_tiling() -> str:
            return self.bind('split', 'split', ',$exit')

        def move_win() -> str:
            return self.bind('move', 'move', '')

        def win_quad() -> str:
            return self.bind('quad', '$win_action', '')

        def move_acts() -> str:
            return self.bind('move_acts', '$win_action', '')

        def layout_wm() -> str:
            return self.bind('layout_wm', 'layout', ',$exit')

        def win_action_wm() -> str:
            return self.bind('win_action_wm', '$win_action', '')

        return i3cfg.mode_binding(mode_bind, mode_name) + \
            i3cfg.mode_start(mode_name) + \
            layout_wm() + \
            split_tiling() + \
            move_win() + \
            move_acts() + \
            win_quad() + \
            win_action_wm() + \
            i3cfg.scratchpad_bindings(mode_name) + \
            i3cfg.circle_bindings(mode_name) + \
            i3cfg.mode_end()

    def mode_default(self, mode_name, mode_bind) -> str:
        _ = mode_bind
        def misc_def() -> str:
            return self.bind('misc_def', '', '')

        def vol_def() -> str:
            return self.bind('vol_def', '$vol', '')

        def win_history_def() -> str:
            return self.bind('win_history_def', '$win_history', '')

        def menu_def() -> str:
            return self.bind('menu_def', '$menu', '')

        def scratchpad_def() -> str:
            return self.bind('scratchpad_def', '$scratchpad', '')

        def focus() -> str:
            return self.bind('focus', 'focus', '')

        def mpd_media() -> str:
            cmd = 'exec --no-startup-id mpc -q'
            return self.bind('mpd_media', cmd, '')

        def mpd_normal() -> str:
            cmd = 'exec --no-startup-id mpc -q'
            return self.bind('mpd_normal', cmd, '')

        def exec_binds() -> str:
            exec_ret = ''
            exec_ret += '\n' \
                + '\n' + mpd_media() \
                + '\n' + mpd_normal() \
                + '\n' + vol_def() \
                + '\n' + menu_def() \
                + '\n' + scratchpad_def() \
                + '\n' + win_history_def()
            exec_ret += '\n'
            key_prog_gui = self.cfg.get('exec', [])
            if key_prog_gui:
                exec_ret += ''.join(map(
                    lambda p:
                    f'bindsym {str(p[0])} exec {str(p[1])}\n',
                    key_prog_gui
                ))
            key_prog = self.cfg.get('exec_no_startup_id', [])
            if key_prog:
                exec_ret += ''.join(map(
                    lambda p:
                    f'bindsym {str(p[0])} exec --no-startup-id {str(p[1])}\n',
                    key_prog
                ))
            exec_ret += '\n'
            return exec_ret

        return misc_def() \
            + focus() \
            + exec_binds() \
            + i3cfg.scratchpad_bindings(mode_name) \
            + i3cfg.circle_bindings(mode_name)
