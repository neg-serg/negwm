import os
from typing import List
from . cfg import cfg
from . extension import extension
from . checker import checker
from . rules import Rules


class conf_gen(extension, cfg):
    self_configured_modules = ['circle', 'scratchpad']
    mode_exit = 'mode "default"'

    def __init__(self, i3) -> None:
        super().__init__()
        cfg.__init__(self, i3)
        self.i3ipc = i3

    def print(self) -> None:
        print(self.generate())

    def write(self) -> None:
        i3_cfg, test_cfg = 'config', '.config_test'
        generated_cfg = self.generate()
        i3_path = f'{os.environ["XDG_CONFIG_HOME"]}/i3'
        with open(f'{i3_path}/{test_cfg}', 'w', encoding='utf8') as fp:
            fp.write(generated_cfg)
        if checker.check_i3_config(cfg=test_cfg):
            with open(f'{i3_path}/' + i3_cfg, 'w', encoding='utf8') as fp:
                fp.write(generated_cfg)
            os.remove(f'{i3_path}/' + test_cfg)

    def generate(self):
        ret = []
        for section in self.cfg.keys():
            if hasattr(self, section):
                section_handler = getattr(self, section)
                if section != 'bindings':
                    ret.append(section_handler())
        ret.append(self.mods_commands())
        binds = self.cfg.get('bindings', {})
        for mode, data in binds.items():
            keybind_data = getattr(self, 'mode_' + mode)(
                mode_name=mode, mode_bind=data.get('bind', None)
            )
            ret.append(keybind_data)
        return '\n'.join(filter(None, ret))

    def plain(self) -> str:
        return self.cfg.get('plain', '').rstrip('\n')

    def colors(self) -> str:
        return self.cfg.get('colors', '').rstrip('\n')

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

    @staticmethod
    def generate_bindsym(mode, tag, settings, p, subtag='', mod='') -> str:
        ret, pref, postfix = '', '', ''
        if mode != 'default':
            pref, postfix = '\t', f', {conf_gen.mode_exit}'
        generate_bindsym = p.split('_')
        mode_, cmd = generate_bindsym[1], generate_bindsym[2]
        if len(generate_bindsym) == 3:
            if mode_ == mode:
                if subtag:
                    subtag = f' {subtag}'
                for keybind in settings[p]:
                    ret += f'{pref}bindsym {keybind.strip()}' + ' ' + \
                        f' ${mod} {cmd.strip()} {tag}{subtag}{postfix}'.strip() + '\n'
        return ret

    @staticmethod
    def module_binds(mode) -> str:
        ret = ''
        for mod_name in conf_gen.self_configured_modules:
            mods = extension.get_mods()
            if mods is None or not mods:
                return ret
            mod = mods[mod_name]
            for tag, settings in mod.cfg.items():
                for param in settings:
                    if isinstance(settings[param], dict):
                        for p in settings[param]:
                            if p.startswith('keybind_'):
                                subtag = param
                                ret += conf_gen.generate_bindsym(
                                    mode, tag, settings[param], p, subtag=subtag, mod=mod_name
                                )
                    elif param.startswith('keybind_'):
                        ret += conf_gen.generate_bindsym(mode, tag, settings, param, mod=mod_name)
        return ret

    def mods_commands(self) -> str:
        ret = ''
        mods = extension.get_mods()
        if mods is None or not mods:
            return ret
        for mod in sorted(mods):
            ret += (f'set ${mod} nop {mod}\n')
        return ret

    def workspaces(self) -> str:
        ret = ''
        workspaces = self.cfg.get('workspaces', [])
        if workspaces:
            for index, ws in enumerate(workspaces):
                ret += f'set ${ws.split(":")[1]} "{index + 1} :: {ws}"\n'
        return ret

    def rules(self) -> str:
        return \
            Rules.rules_mod('scratchpad') + \
            Rules.rules_mod('circle') + \
            self.cfg.get('rules', '').rstrip('\n')

    @staticmethod
    def mode(name='', keymap='', start=False, end=False):
        if not start and not end:
            return f'bindsym {keymap} mode "{name}"\n'
        if start:
            return 'mode ' + name + ' {'
        if end:
            ret = ''
            pref = '\t'
            bindings = ['Return', 'Escape', 'space', 'Control+C', 'Control+G']
            for keybind in bindings:
                ret += f'{pref}bindsym {keybind}, {conf_gen.mode_exit}\n'
            return ret + '}\n'
        return ''

    def bind_mode(self, section_name, exit=False, mode=True):
        return self.bind(section_name, exit, mode)

    def bind(self, section_name, exit=False, mode=False) -> str:
        ret = ''
        prefix = f'\tbindsym' if mode else 'bindsym'
        end = '' if not exit else f', {conf_gen.mode_exit}'
        section = self.cfg.get(section_name, {})
        s = section_name.split(':')
        mod, name = s[0], s[1]
        section = self.cfg.get('bindings', {}).get(mod, {}).get(name, {})
        if section:
            ret += '\n'
            action_prefix = section.get('action_prefix', '')
            for key, val in section.items():
                print(f'key={key}, val={val}')
                if key == 'action_prefix':
                    continue
                if isinstance(val, str) and isinstance(key, str):
                    # key: binding, val: action
                    ret += f'{prefix} {key} {action_prefix} {val}{end}\n'
                if isinstance(val, list) and not isinstance(key, tuple):
                    for keymap in val:
                        ret += f'{prefix} {keymap} {action_prefix} {key}{end}\n'
                elif isinstance(val, dict):
                    param = ' ' + val.get('param', '')
                    binds = val.get('binds', [])
                    for k in binds:
                        ret += f'{prefix} {k} {action_prefix} {key}{param}{end}\n'
        return ret

    def mode_default(self, mode_name, mode_bind) -> str:
        _ = mode_bind
        return self.bind(f'{mode_name}:exec') + \
            self.bind(f'{mode_name}:exec_no_startup_id') + \
            self.bind(f'{mode_name}:focus') + \
            self.bind(f'{mode_name}:i3') + \
            self.bind(f'{mode_name}:vol') + \
            self.bind(f'{mode_name}:remember_focused') + \
            self.bind(f'{mode_name}:scratchpad') + \
            self.bind(f'{mode_name}:menu') + \
            self.bind(f'{mode_name}:misc') + \
            self.bind(f'{mode_name}:media') + \
            self.bind(f'{mode_name}:media_xf86') + \
            conf_gen.module_binds(mode_name)

    def mode_resize(self, mode_name, mode_bind) -> str:
        return conf_gen.mode(mode_name, mode_bind) + \
            conf_gen.mode(mode_name, start=True) + \
            self.bind_mode(f'{mode_name}:plus') + \
            self.bind_mode(f'{mode_name}:minus') + \
            conf_gen.mode(end=True)

    def mode_spec(self, mode_name, mode_bind) -> str:
        return conf_gen.mode(mode_name, mode_bind) + \
            conf_gen.mode(mode_name, start=True) + \
            self.bind_mode(f'{mode_name}:misc', exit=True) + \
            self.bind_mode(f'{mode_name}:menu', exit=True) + \
            conf_gen.module_binds(mode_name) + \
            conf_gen.mode(end=True)

    def mode_wm(self, mode_name, mode_bind) -> str:
        return conf_gen.mode(mode_name, mode_bind) + \
            conf_gen.mode(mode_name, start=True) + \
            self.bind_mode(f'{mode_name}:layout', exit=True) + \
            self.bind_mode(f'{mode_name}:split', exit=True) + \
            self.bind_mode(f'{mode_name}:move') + \
            self.bind_mode(f'{mode_name}:actions') + \
            conf_gen.module_binds(mode_name) + \
            conf_gen.mode(end=True)
