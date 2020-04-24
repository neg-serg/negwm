#!/usr/bin/python3

import os
from typing import List
import textwrap

from misc import Misc
from cfg import cfg
from extension import extension
from lib.checker import checker

class i3cfg(extension, cfg):
    def __init__(self, i3) -> None:
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
        with open(test_cfg, 'w', encoding='utf8') as fp:
            fp.write(generated_cfg)
        if checker.check_i3_config(verbose=False, cfg=test_cfg):
            with open(i3_cfg, 'w', encoding='utf8') as fp:
                fp.write(generated_cfg)
            os.remove(Misc.i3path() + test_cfg)

    def generate(self):
        ret = []
        cfg_sections = self.cfg.get('sections', [])
        if cfg_sections:
            for section in cfg_sections:
                section_data = getattr(self, section)()
                ret.append(textwrap.dedent(section_data))
        bind_modes = self.cfg.get('bind_modes', [])
        for keybind in bind_modes:
            bind_name, mode_bind = keybind[0], keybind[1]
            keybind_data = getattr(self, 'mode_' + bind_name)(
                mode_name=bind_name, mode_bind=mode_bind
            )
            ret.append(textwrap.dedent(keybind_data))
        return ret

    def autostart(self) -> str:
        return '\n'.join(self.cfg.get('autostart', [])) + '\n'

    def gaps(self) -> str:
        gaps = [0, 0, 0, 0]
        gaps_params = [
            f'gaps inner {gaps[0]}',
            f'gaps outer {gaps[1]}',
            f'gaps top {gaps[2]}',
            f'gaps bottom {gaps[3]}'
        ]
        return '\n'.join(gaps_params) + '\n'

    def general(self) -> str:
        return '\n'.join(self.cfg.get('general', [])) + '\n'

    def focus_settings(self) -> str:
        return '\n'.join(self.cfg.get('focus_settings', [])) + '\n'

    def theme(self) -> str:
        theme = '\n'.join(self.cfg.get('theme', [])) + '\n'
        color_theme = {
            'client.focused': [
                '#222233', '#000000', '#ddddee', '#112211', '#0C0C0D'
            ],
            'client.focused_inactive': [
                '#000000', '#000000', '#005fff', '#000000', '#222233'
            ],
            'client.unfocused': [
                '#000000', '#000000', '#315c70', '#000000', '#222233'
            ],
            'client.urgent': [
                '#000000', '#2E2457', '#4C407C', '#32275E', '#32275E'
            ],
            'client.placeholder': [
                '#000000', '#0c0c0c', '#ffffff', '#000000', '#0c0c0c'
            ],
            'client.background': ['#000000'],
        }
        theme_ret = ''
        for param, data in color_theme.items():
            theme_ret += f"{param} {' '.join(data)}\n"
        return theme + theme_ret

    def bscratch_bindings(self, mode) -> str:
        ret = ''
        def get_binds(mode, tag, settings, p, subtag='') -> str:
            ret = ''
            pref, postfix = '', ''
            if mode != 'default':
                pref, postfix = '\t', ', $exit'
            get_binds = p.split('_')
            mode_ = get_binds[1]
            cmd = get_binds[2]
            if len(get_binds) == 3:
                if mode_ == mode:
                    for keybind in settings[p]:
                        ret += f'{pref.strip()}bindsym {keybind.strip()}' \
                            f' $bscratch {cmd.strip()} {tag.strip()} ' \
                            f'{subtag.strip()} {postfix.strip()}\n'
            return ret

        bscratch = extension.get_mods()['bscratch']
        for tag,settings in bscratch.cfg.items():
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

    def circle_bindings(self, mode) -> str:
        ret = ''
        def get_binds(mode, tag, settings, p, subtag='') -> str:
            ret = ''
            pref, postfix = '', ''
            if mode != 'default':
                pref, postfix = '\t', ', $exit'
            get_binds = p.split('_')
            mode_ = get_binds[1]
            cmd = get_binds[2]
            if len(get_binds) == 3:
                if mode_ == mode:
                    for keybind in settings[p]:
                        ret += f'{pref}bindsym {keybind} $circle' \
                            f' {cmd} {tag} {subtag} {postfix}\n'
            return textwrap.dedent(ret)

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
        return textwrap.dedent(ret)

    def mods_commands(self) -> str:
        ret = ''
        for mod in sorted(extension.get_mods()):
            ret += (f'set ${mod} exec --no-startup-id {self.send_path} {mod}\n')
        return textwrap.dedent(ret)

    def workspaces(self) -> str:
        ret = ''
        for index, ws in enumerate(self.cfg['ws_list']):
            ret += f'set ${ws.split(":")[1]} "{index + 1} :: {ws}"\n'
        return textwrap.dedent(ret)

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
            return ret, cmd_dict, mod

        def rules_bscratch() -> str:
            """ Create i3 match rules for all tags. """
            ret, cmd_dict, bscratch = rules_mod('bscratch')
            ret += '\n'
            for tag in cmd_dict:
                geom = bscratch.nsgeom.get_geom(tag)
                ret += f'for_window $bscratch-{tag} move scratchpad, {geom}\n'
            return ret

        def rules_circle() -> str:
            ret, _, circle = rules_mod('circle')
            for tag in circle.cfg:
                focus_cmd = ''
                ws = circle.cfg[tag].get('ws', '')
                focus = bool(circle.cfg[tag].get('focus', True))
                if focus:
                    focus_cmd = ', focus'
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
        return textwrap.dedent(
            rules_bscratch() + \
            rules_circle() + \
            plain_rules()
        )


    def mode_start(self, name) -> str:
        return 'mode ' + name + ' {\n'

    def mode_end(self) -> str:
        ret = ''
        bindings = ['Return', 'Escape', 'space', 'Control+C', 'Control+G']
        for keybind in bindings:
            ret += f'bindsym {keybind} $exit\n'
        return ret + '}\n'

    def mode_binding(self, keymap, name) -> str:
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
                            f'{funcs[i]} {param_str}{end}\n'
                ret += '\n'
        return ret

    def mode_resize(self, mode_name, mode_bind) -> str:
        def bind_data():
            ret = ''
            funcs = ['left', 'bottom', 'top', 'right']
            resize_cfg = self.cfg.get('resize', {})
            if resize_cfg:
                step = resize_cfg.get('step', '')
                binds = resize_cfg.get('binds', [])
                win_action = extension.get_mods().get('win_action', '')
                if step and binds:
                    if win_action:
                        for bind in binds:
                            for i, key in enumerate(bind):
                                ret += f'bindsym {key} $win_action ' \
                                    f'resize {funcs[i]} {step}\n'
                            for i, key in enumerate(bind):
                                ret += f'bindsym Shift+{key} $win_action ' \
                                    f'resize {funcs[i]} -{step}\n'
                            ret += '\n'
                    ret +=textwrap.dedent("""\
                    bindsym semicolon resize shrink right 4
                    bindsym Shift+colon resize grow right 4
                    """)
            return ret

        return textwrap.dedent(
            self.mode_binding(mode_bind, mode_name) + \
            self.mode_start(mode_name) + \
            bind_data() + \
            self.mode_end()
        )

    def mode_spec(self, mode_name, mode_bind) -> str:
        def menu_spec() -> str:
            return self.bind('menu_spec', '$menu', ', $exit')

        def misc_spec() -> str:
            return self.bind('misc_spec', '', ', $exit')

        return textwrap.dedent(
            self.mode_binding(mode_bind, mode_name) + \
            self.mode_start(mode_name) + \
            misc_spec() + \
            menu_spec() + \
            self.bscratch_bindings(mode_name) + \
            self.circle_bindings(mode_name) + \
            self.mode_end()
        )

    def mode_wm(self, mode_name, mode_bind) -> str:
        def split_tiling() -> str:
            return self.bind('split', 'split', ', $exit')

        def move_win() -> str:
            return self.bind('move', 'move', '')

        def win_quad() -> str:
            return self.bind('quad', '$win_action', '')

        def move_acts() -> str:
            return self.bind('move_acts', '$win_action', '')

        def layout_wm() -> str:
            return self.bind('layout_wm', 'layout', ', $exit')

        def win_action_wm() -> str:
            return self.bind('win_action_wm', '$win_action', '')

        def bind_data() -> str:
            ret = ''
            ret += layout_wm() + \
                split_tiling() + \
                move_win()
            win_action = extension.get_mods().get('win_action', '')
            if win_action:
                ret += move_acts() + \
                    win_quad() + \
                    win_action_wm()
            return ret

        return textwrap.dedent(
            self.mode_binding(mode_bind, mode_name) + \
            self.mode_start(mode_name) + \
            bind_data() + \
            self.bscratch_bindings(mode_name) + \
            self.circle_bindings(mode_name) + \
            self.mode_end()
        )

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

        def bscratch_def() -> str:
            return self.bind('bscratch_def', '$bscratch', '')

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
                + '\n' + bscratch_def() \
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

        return textwrap.dedent(
            misc_def() \
            + focus() \
            + exec_binds() \
            + self.bscratch_bindings(mode_name) \
            + self.circle_bindings(mode_name)
        )

