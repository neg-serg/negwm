#!/usr/bin/python3

from cfg import cfg
from extension import extension
from misc import Misc
from typing import List
import textwrap

class i3cfg(extension, cfg):
    def __init__(self, i3) -> None:
        cfg.__init__(self, i3)
        # i3ipc connection, bypassed by negi3wm runner
        self.i3ipc = i3

        self.bindings = {
            "show": self.show_cfg,
            "write":self.write_cfg,
        }

        self.send_path = '${XDG_CONFIG_HOME}/i3/bin/send'

    def generate(self):
        ret = []
        cfg_sections = self.cfg.get('sections', [])
        if cfg_sections:
            for section in cfg_sections:
                section_data = getattr(self, section)()
                ret.append(textwrap.dedent(section_data))
        return ret

    def show_cfg(self) -> None:
        print(''.join(self.generate()))

    def write_cfg(self) -> None:
        i3_config = '/home/neg/.config/i3/config'
        with open(i3_config, 'w', encoding='utf8') as outfile:
            outfile.write('\n'.join(self.generate()))

    def autostart(self) -> str:
        autostart_list = self.cfg.get('autostart', [])
        return '\n'.join(autostart_list) + '\n'

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
        ret = self.cfg.get('general', [])
        return '\n'.join(ret) + '\n'

    def focus_settings(self) -> str:
        ret = self.cfg.get('focus_settings', [])
        return '\n'.join(ret) + '\n'

    def colorscheme(self) -> str:
        ret = self.cfg.get('appearance', [])
        appearance = '\n'.join(ret) + '\n'
        theme = {
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
        colorscheme = ''
        for param, data in theme.items():
            colorscheme += f"{param} {' '.join(data)}\n"

        return textwrap.dedent(appearance) \
            + textwrap.dedent(colorscheme)

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
                        ret += f'{pref.strip()} bindsym {keybind.strip()}' \
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
        return textwrap.dedent(ret)

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

    def font(self) -> str:
        return "font pango: Iosevka Term Heavy 9"

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
        """ Returns cmd needed to hide scratchpad.
            Args:
                hide (bool): to hide target or not.
        """
        ret = ""
        if hide:
            ret = ", [con_id=__focused__] scratchpad show"
        return ret

    def rules(self) -> str:
        def fill_rules_dict(mod, cmd_dict) -> List:
            config = mod.cfg
            for tag in config:
                cmd_dict[tag] = []
                for attr in config[tag]:
                    for target_attr in ['class', 'instance', 'name', 'role']:
                        cmd_dict[tag].append(info(
                            config, tag, attr, target_attr
                        ))
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
                ret += f'for_window $bscratch-{tag} move scratchpad, {geom}'
                ret += '\n'
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

        def info(config: dict, tag: str, attr: str, target_attr: str) -> str:
            """ Create rule in i3 commands format
                Args:
                    config (dict): extension config.
                    tag (str): target tag.
                    attr (str): tag attrubutes.
                    target_attr (str): attribute to fill.
            """
            conv_dict_attr = {
                'class': 'class',
                'instance': 'instance',
                'name': 'window_name',
                'role': 'window_role'
            }
            cmd = ''
            if target_attr in attr:
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
            return self.cfg.get('plain_rules', '')

        ret = ''
        ret += \
            textwrap.dedent(rules_bscratch()) + \
            textwrap.dedent(rules_circle()) + \
            textwrap.dedent(plain_rules())
        return textwrap.dedent(ret)


    def keybindings_mode_start(self, name) -> str:
        return 'mode ' + name + ' {\n'

    def keybindings_mode_end(self) -> str:
        def bind_data() -> str:
            ret = ''
            bindings = ['Return', 'Escape', 'space', 'Control+C', 'Control+G']
            for keybind in bindings:
                ret += f'bindsym {keybind} $exit\n'
            return ret
        return bind_data() + '}\n'

    def keybindings_mode_binding(self, keymap, name) -> str:
        return f'bindsym {keymap} mode "{name}"\n'

    def keybindings_mode_resize(self) -> str:
        mode_bind = 'Mod4+r'
        mode_name = 'RESIZE'

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

        ret = ''
        ret += self.keybindings_mode_binding(mode_bind, mode_name)
        ret += self.keybindings_mode_start(mode_name)
        ret += str(bind_data())
        ret += str(self.keybindings_mode_end())

        return textwrap.dedent(ret)

    def keybindings_mode_spec(self) -> str:
        mode_bind = 'Mod1+e'
        mode_name = 'SPEC'

        def menu_spec() -> str:
            return self.bind('menu_spec', '$menu', ', $exit')

        def bind_data():
            return """
            bindsym c exec rofi-pass; $exit
            bindsym e [urgent=latest] focus, $exit

            bindsym Shift+d floating toggle, $exit
            bindsym Shift+l exec sh -c 'sudo gllock', $exit
            """

        ret = ''
        ret += self.keybindings_mode_binding(mode_bind, mode_name)
        ret += self.keybindings_mode_start(mode_name)
        ret += str(bind_data())
        ret += menu_spec()
        ret += str(self.bscratch_bindings(mode_name))
        ret += str(self.circle_bindings(mode_name))
        ret += self.keybindings_mode_end()

        return textwrap.dedent(ret)

    def bind(self, section_name, post, end, pre='bindsym') -> str:
        ret = ''
        section = self.cfg.get(section_name, {})
        if section:
            binds = section.get('binds', [])
            funcs = section.get('funcs')
            modkey = section.get('modkey', '')
            if modkey:
                modkey += '+'
            if binds and funcs:
                ret += '\n'
                for bind in binds:
                    for i, key in enumerate(bind):
                        ret += f'{pre} {modkey}{key} {post} {funcs[i]}{end}\n'
                ret += '\n'
        return ret

    def keybindings_mode_wm(self) -> str:
        mode_bind = 'Mod4+minus'
        mode_name = 'WM'

        def split_tiling() -> str:
            return self.bind('split', 'split', ', $exit')

        def move_win() -> str:
            return self.bind('move', 'move', '')

        def win_quad() -> str:
            return self.bind('quad', '$win_action', '')

        def move_acts() -> str:
            ret = ''
            move_acts = self.cfg.get('move_acts', {})
            if move_acts:
                binds = move_acts.get('binds', [])
                funcs = move_acts.get('funcs')
                coeff = move_acts.get('coeff', '')
                modkey = move_acts.get('modkey', '')
                if modkey:
                    modkey += '+'
                if binds and funcs and coeff:
                    ret += '\n'
                    for bind in binds:
                        for i, key in enumerate(bind):
                            ret += f'bindsym {key} $win_action {coeff} ' \
                                f'{funcs[i]}\n'
                        ret += '\n'
            return ret

        def layout_wm() -> str:
            return self.bind('layout_wm', 'layout', ', $exit')

        def win_action_wm() -> str:
            return self.bind('win_action_wm', '$win_action', '')

        def bind_data() -> str:
            ret = ''
            ret += layout_wm()
            ret += split_tiling()
            ret += move_win()
            win_action = extension.get_mods().get('win_action', '')
            if win_action:
                ret += move_acts()
                ret += win_quad()
                ret += win_action_wm()
            return ret

        ret = ''
        ret += self.keybindings_mode_binding(mode_bind, mode_name)
        ret += self.keybindings_mode_start(mode_name)
        ret += str(bind_data())
        ret += str(self.bscratch_bindings(mode_name))
        ret += str(self.circle_bindings(mode_name))
        ret += self.keybindings_mode_end()

        return textwrap.dedent(ret)

    def keybindings_mode_default(self) -> str:
        mode_name = 'default'

        def bind_data() -> str:
            return """
            bindsym Mod4+q fullscreen toggle
            bindsym Mod4+Control+q kill
            """

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
            exec_ret += self.cfg.get('exec_binds','')
            exec_ret += '\n'

            return exec_ret

        ret = ''
        ret += str(textwrap.dedent(bind_data()))
        ret += str(textwrap.dedent(focus()))
        ret += str(textwrap.dedent(exec_binds()))
        ret += str(self.bscratch_bindings(mode_name))
        ret += str(self.circle_bindings(mode_name))

        return textwrap.dedent(ret)

