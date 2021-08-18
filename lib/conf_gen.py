import os
from typing import List
from . misc import Misc
from . cfg import cfg
from . extension import extension
from . checker import checker

class conf_gen(extension, cfg):
    def __init__(self, i3) -> None:
        super().__init__()
        cfg.__init__(self, i3)
        self.i3ipc = i3
        self.bindings = {
            "print": self.print,
            "dump": self.dump_cfg,
            "reload": self.reload_config,
        }
        self.send_path = '${XDG_CONFIG_HOME}/negi3wm/bin/send'

    def print(self) -> None:
        print(''.join(self.generate()))

    def dump_cfg(self) -> None:
        i3_cfg, test_cfg = 'config', '.config_test'
        generated_cfg = '\n'.join(self.generate())
        i3_path = f'{os.environ["XDG_CONFIG_HOME"]}/i3'
        with open(f'{i3_path}/{test_cfg}', 'w', encoding='utf8') as fp:
            fp.write(generated_cfg)
        if checker.check_i3_config(verbose=False, cfg=test_cfg):
            with open(f'{i3_path}/' + i3_cfg, 'w', encoding='utf8') as fp:
                fp.write(generated_cfg)
            os.remove(f'{i3_path}/' + test_cfg)

    def generate(self):
        ret = []
        for section in ["general", "workspaces", "colors", "mods_commands", "rules", "startup"]:
            section_data = getattr(self, section)()
            ret.append(section_data)
        bind_modes = self.cfg.get('bind_modes', {})
        for name, keybind in bind_modes.items():
            keybind_data = getattr(self, 'mode_' + name)(
                mode_name=name, mode_bind=keybind
            )
            ret.append(keybind_data)
        return ret

    def general(self) -> str:
        return '\n'.join(self.cfg.get('general', [])) + '\n'

    def startup(self) -> str:
        ret = ''
        startup = self.cfg.get('startup', {})
        once, always = startup.get('once', {}), startup.get('always', {})
        if once:
            for exe in once.values():
                ret += f'exec {exe}\n'
        if always:
            for exe in always.values():
                ret += f'exec_always {exe}\n'
        return ret.rstrip('\n')

    def colors(self) -> str:
        ret = ''
        for key, values in self.cfg.get('colors', {}).items():
            ret += 'client.' + key + ' ' + ' '.join(str(val) for val in values) + '\n'
        return ret.rstrip("\n")

    @staticmethod
    def scratchpad_bindings(mode) -> str:
        ret = ''
        def get_binds(mode, tag, settings, p, subtag='') -> str:
            ret = ''
            pref, postfix = '', ''
            if mode != 'default':
                pref, postfix = '\t', ',$exit'
            get_binds = p.split('_')
            mode_, cmd = get_binds[1], get_binds[2]
            if len(get_binds) == 3:
                if mode_ == mode:
                    if subtag:
                        subtag = f' {subtag}'
                    for keybind in settings[p]:
                        ret += f'{pref}bindsym {keybind.strip()}' + ' ' + \
                            f' $scratchpad {cmd.strip()} {tag}{subtag}{postfix}'.strip() + '\n'
            return ret

        mods = extension.get_mods()
        if mods is None or not mods:
            return ret
        scratchpad = mods['scratchpad']
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
            mode_, cmd = get_binds[1], get_binds[2]
            if len(get_binds) == 3:
                if mode_ == mode:
                    if subtag:
                        subtag = f' {subtag}'
                    for keybind in settings[p]:
                        ret += f'{pref}bindsym {keybind} $circle' + ' ' + \
                            f' {cmd} {tag}{subtag}{postfix}'.strip() + '\n'
            return ret

        mods = extension.get_mods()
        if mods is None or not mods:
            return ret
        circle = mods['circle']
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
        mods = extension.get_mods()
        if mods is None or not mods:
            return ret
        for mod in sorted(mods):
            ret += (f'set ${mod} exec --no-startup-id {self.send_path} {mod}\n')
        return ret

    def workspaces(self) -> str:
        ret = ''
        for index, ws in enumerate(self.cfg['workspaces']):
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
            mods = extension.get_mods()
            if mods is None or not mods:
                return ret
            mod = mods.get(modname, None)
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
                    geom = getattr(scratchpad, 'nsgeom').get_geom(tag)
                    ret += f'for_window $scratchpad-{tag}' + \
                        f' move scratchpad, {geom}\n'
                else:
                    ret += f'for_window $scratchpad-{tag} floating enable\n'
            return ret

        def rules_circle() -> str:
            (ret, _, circle) = rules_mod('circle')
            conf = getattr(circle, 'cfg')
            for tag in conf:
                focus_cmd = ''
                ws = conf[tag].get('ws', '')
                focus = bool(conf[tag].get('focus', True))
                if focus:
                    focus_cmd = ',focus'
                if ws:
                    ret += f'for_window $circle-{tag}' \
                        f' move workspace ${ws}{focus_cmd}\n'
            return ret

        def info(config: dict, tag: str, attr: str, fill: str) -> str:
            """ Create rule in i3 commands format
                config (dict): extension config.
                tag (str): target tag.
                attr (str): tag attrubutes.
                fill (str): attribute to fill. """
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

        def rules() -> str:
            ret = ''
            rules = self.cfg.get('rules', {})
            if rules:
                for rule, action in rules.items():
                    ret += f'for_window {rule} {action}\n'
            return ret

        return rules_scratchpad() + rules_circle() + rules()

    @staticmethod
    def mode_start(name) -> str:
        return 'mode ' + name + ' {'

    @staticmethod
    def mode_end() -> str:
        ret = ''
        pref = '\t'
        bindings = ['Return', 'Escape', 'space', 'Control+C', 'Control+G']
        for keybind in bindings:
            ret += f'{pref}bindsym {keybind},$exit\n'
        return ret + '}\n'

    @staticmethod
    def mode_binding(keymap, name) -> str:
        return f'bindsym {keymap} mode "{name}"\n'

    def bind(self, section_name, post, end, pre='bindsym') -> str:
        ret = ''
        section = self.cfg.get(section_name, {})
        if section:
            modkey = section.get('modkey', '')
            param = section.get('param', '')
            if modkey:
                modkey += '+'
            if param:
                param = ' ' + param
            ret += '\n'
            keymaps = section.get('keymap', {})
            if keymaps:
                for action, maps in keymaps.items():
                    for keymap in maps:
                        ret += f'{pre} {modkey}{keymap} {post} {action}{param}{end}\n'
        return ret


    def mode_default(self, mode_name, mode_bind) -> str:
        _ = mode_bind

        def exec_bindings() -> str:
            exec_ret = ''
            exec_ret += \
            self.bind('media', 'exec --no-startup-id playerctl', '') + \
                self.bind('vol', '$vol', '') + \
                self.bind('menu', '$menu', '') + \
                self.bind('scratchpad', '$scratchpad', '') + \
                self.bind('remember_focused', '$remember_focused', '')
            execs = self.cfg.get('exec', {})
            if execs:
                plain = execs.get('plain', {})
                if plain:
                    for bind, prog in plain.items():
                        exec_ret += f'bindsym {bind} exec {prog}\n'
                no_startup_id = execs.get('no_startup_id', {})
                for bind, prog in no_startup_id.items():
                    exec_ret += f'bindsym {bind} exec {prog}\n'
            return exec_ret

        return \
            self.bind('misc', '', '') + \
            self.bind('focus', 'focus', '') + \
            exec_bindings() + \
            conf_gen.scratchpad_bindings(mode_name) + \
            conf_gen.circle_bindings(mode_name)

    def mode_resize(self, mode_name, mode_bind) -> str:
        return conf_gen.mode_binding(mode_bind, mode_name) + \
            conf_gen.mode_start(mode_name) + \
            self.bind('resize_plus', '$actions resize', '', pre='\tbindsym') + \
            self.bind('resize_minus', '$actions resize', '', pre='\tbindsym') + \
            conf_gen.mode_end()

    def mode_spec(self, mode_name, mode_bind) -> str:
        return conf_gen.mode_binding(mode_bind, mode_name) + \
            conf_gen.mode_start(mode_name) + \
            self.bind('misc_spec', '', ',$exit', pre='\tbindsym') + \
            self.bind('menu_spec', '$menu', ',$exit', pre='\tbindsym') + \
            conf_gen.scratchpad_bindings(mode_name) + \
            conf_gen.circle_bindings(mode_name) + \
            conf_gen.mode_end()

    def mode_wm(self, mode_name, mode_bind) -> str:
        return conf_gen.mode_binding(mode_bind, mode_name) + \
            conf_gen.mode_start(mode_name) + \
            self.bind('layout_wm', 'layout', ',$exit', pre='\tbindsym') + \
            self.bind('split', 'split', ',$exit', pre='\tbindsym') + \
            self.bind('move', 'move', '', pre='\tbindsym') + \
            self.bind('move_acts', '$actions', '', pre='\tbindsym') + \
            self.bind('quad', '$actions', '', pre='\tbindsym') + \
            self.bind('actions_wm', '$actions', '', pre='\tbindsym') + \
            conf_gen.scratchpad_bindings(mode_name) + \
            conf_gen.circle_bindings(mode_name) + \
            conf_gen.mode_end()
