import os
from . misc import Misc
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

    def print(self) -> None: print(self.generate())

    def write(self) -> None:
        cfg, test_cfg = 'config', '.config_test'
        generated_cfg = self.generate()
        with open(f'{Misc.i3path()}/{test_cfg}', 'w', encoding='utf8') as fp:
            fp.write(generated_cfg)
        if checker.check_i3_config(cfg=test_cfg):
            with open(f'{Misc.i3path()}/{cfg}', 'w', encoding='utf8') as fp:
                fp.write(generated_cfg)
            os.remove(f'{Misc.i3path()}/{test_cfg}')

    def generate(self):
        ret = []
        for cfg_section in self.cfg.keys():
            if cfg_section.startswith('mode_'):
                ret.append(self.bind(cfg_section))
            if hasattr(self, cfg_section):
                cfg_section_handler = getattr(self, cfg_section)
                ret.append(cfg_section_handler())
        ret.append(self.mods_commands())

        return '\n'.join(filter(None, ret))

    def plain(self) -> str: return self.cfg.get('plain', '').rstrip('\n')
    def colors(self) -> str: return self.cfg.get('colors', '').rstrip('\n')

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
        bind_data = p.split('_')[1:]
        if subtag:
            subtag = f' {subtag}'
        if mode != 'default' and bind_data[0] == mode:
            pref, postfix = '\t', f', {conf_gen.mode_exit}'
            cmd = bind_data[1]
            for keybind in settings[p]:
                ret += f'{pref}bindsym {keybind.strip()} ' + \
                    f' ${mod} {cmd.strip()} {tag}{subtag}{postfix}'.strip() + '\n'
        else:
            if len(bind_data) == 1 and mode == 'default':
                cmd = bind_data[0]
                for keybind in settings[p]:
                    ret += f'bindsym {keybind.strip()} ' + \
                        f' ${mod} {cmd.strip()} {tag}{subtag}'.strip() + '\n'
        return ret

    @staticmethod
    def module_binds(mode) -> str:
        ret = ''
        mods = extension.get_mods()
        if mods is None or not mods:
            return ret
        for mod_name in conf_gen.self_configured_modules:
            mod = mods[mod_name]
            for tag, settings in mod.cfg.items():
                for param in settings:
                    if isinstance(settings[param], dict):
                        for param_name in settings[param]:
                            if param_name.startswith('keybind_'):
                                ret += conf_gen.generate_bindsym(
                                    mode, tag, settings[param], param_name, subtag=param, mod=mod_name
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
            ret = f'{ret}set ${mod} nop {mod}\n'
        return ret

    def workspaces(self) -> str:
        ret = ''
        workspaces = self.cfg.get('workspaces', [])
        if workspaces:
            for index, ws in enumerate(workspaces):
                ret = f'{ret}set ${ws.split(":")[1]} "{index + 1} :: {ws}"\n'
        return ret

    def rules(self) -> str:
        return \
            Rules.rules_mod('scratchpad') + \
            Rules.rules_mod('circle') + \
            self.cfg.get('rules', '').rstrip('\n')

    def mode(self, name, bind='', end=False):
        ret = ''
        name = name.removeprefix('mode_')
        if name == 'default':
            return ret
        if not end:
            if bind:
                ret = f'{ret}bindsym {bind} mode "{name}"\n'
            return f'{ret}mode {name} {{'
        else:
            bindings = ['Return', 'Escape', 'space', 'Control+C', 'Control+G']
            for keybind in bindings:
                ret = f'{ret}\tbindsym {keybind}, {conf_gen.mode_exit}\n'

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
