import os
from . cfg import cfg
from . extension import extension
from . checker import checker
from . rules import Rules
from . keymap import keymap as Keymap


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
        for cfg_section in self.cfg.keys():
            if cfg_section.startswith('mode_'):
                ret.append(self.bind(cfg_section))
            if hasattr(self, cfg_section):
                cfg_section_handler = getattr(self, cfg_section)
                ret.append(cfg_section_handler())
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

    def exec_always(self) -> str:
        ret = ''
        exec_always = self.cfg.get('exec_always', {})
        if exec_always:
            for exe in exec_always:
                ret += f'exec_always {exe}\n'
        return ret.rstrip('\n')

    def exec(self) -> str:
        ret = ''
        exec = self.cfg.get('exec', {})
        if exec:
            for exe in exec:
                ret += f'exec {exe}\n'
        return ret.rstrip('\n')

    @staticmethod
    def generate_bindsym(mode, tag, settings, p, subtag='', mod='') -> str:
        ret, pref, postfix = '', '', ''
        mode = mode.removeprefix('mode_')
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

    def mode(self, name='', bind='',  end=False):
        ret = ''
        name = name.removeprefix('mode_')
        if name == 'default':
            return ret
        if not end:
            if bind:
                ret += f'bindsym {bind} mode "{name}"\n'
            return f'{ret}mode {name} {{'
        else:
            bindings = ['Return', 'Escape', 'space', 'Control+C', 'Control+G']
            for keybind in bindings:
                ret += f'\tbindsym {keybind}, {conf_gen.mode_exit}\n'

            return ret + '}\n'

    def bind(self, mod) -> str:
        section = self.cfg.get(mod, {})
        ret = f'{self.mode(mod, bind=section.bind, end=False)}'
        prefix = f'\tbindsym' if mod != 'mode_default' else 'bindsym'
        for param in section:
            ret += '\n'
            kmap = section[param]
            end = f', {conf_gen.mode_exit}' if kmap.exit else ''
            for key, val in kmap.items():
                if isinstance(val, str) and isinstance(key, str):
                    # key: binding, val: action
                    if '{cmd}' not in kmap.fmt:
                        ret += f'{prefix} {key} {kmap.fmt} {val}{end}\n'
                    else:
                        format = kmap.fmt
                        format = format.replace('{cmd}', val)
                        ret += f'{prefix} {key} {format}{end}\n'
                if isinstance(val, list) and not isinstance(key, tuple):
                    for b in val:
                        if '{cmd}' not in kmap.fmt:
                            ret += f'{prefix} {b} {kmap.fmt} {key}{end}\n'
                        else:
                            format = kmap.fmt
                            format = format.replace('{cmd}', key)
                            ret += f'{prefix} {b} {format}{end}\n'

        ret += f'{conf_gen.module_binds(mod)}{self.mode(mod, end=True)}'

        return ret
