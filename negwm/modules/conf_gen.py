import os

from negwm.lib.misc import Misc
from negwm.lib.cfg import cfg
from negwm.lib.extension import extension
from negwm.lib.checker import checker
from negwm.lib.rules import Rules
from negwm.lib.keymap import bindmap as Bindmap


class conf_gen(extension, cfg):
    self_configured_modules=['circle', 'scratchpad']
    mode_exit='mode "default"'

    def __init__(self, i3) -> None:
        super().__init__()
        cfg.__init__(self, i3)
        self.i3ipc=i3
        self.conf_data=[]

    def print(self) -> None: print(self.generate_config())

    def write(self):
        cfg, test_cfg = 'config', '.config_test'
        generated_cfg = self.generate_config()
        with open(f'{Misc.i3path()}/{test_cfg}', 'w', encoding='utf8') as fp:
            fp.write(generated_cfg)
        if checker.check_i3_config(cfg=test_cfg):
            with open(f'{Misc.i3path()}/{cfg}', 'w', encoding='utf8') as fp:
                fp.write(generated_cfg)
            os.remove(f'{Misc.i3path()}/{test_cfg}')

    @staticmethod
    def text_section(text: str):
        if text is None:
            text=''
        return text

    def fill(self, section='', bind=False, text='', module_bindings=False) -> None:
        if module_bindings:
            mods=extension.get_mods()
            if mods is None or not mods:
                pass
            for mod in sorted(mods):
                self.conf_data.append(f'set ${mod} nop {mod}')
            return
        if section.startswith('mode_'):
            bind=True
        if bind:
            self.conf_data.append(self.bind(section))
            return
        if text:
            self.conf_data.append(conf_gen.text_section(text))
            return
        if hasattr(self, section):
            section_handler=getattr(self, section)
            self.conf_data.append(section_handler())
            return

    def generate_config(self) -> str:
        self.cfg_cleanup()
        self.fill(text='# [Generated by negwm with default generator]\n')
        self.fill(text=self.cfg.get('plain',''))
        for cfg_section in self.cfg.keys():
            self.fill(cfg_section)
        self.fill(module_bindings=True)
        self.fill(text='# vim:filetype=i3config\n')
        return '\n'.join(filter(None, self.conf_data))

    def exec(self) -> str:
        ret = ''
        exec = self.cfg.get('exec', {})
        if exec:
            for exe in exec:
                ret += f'exec {exe}\n'
        exec_always = self.cfg.get('exec_always', {})
        if exec_always:
            for exe in exec_always:
                ret += f'exec_always {exe}\n'
        return ret.rstrip('\n')

    def cfg_cleanup(self) -> None:
        self.conf_data=[]

    @staticmethod
    def generate_bindsym(mode, tag, settings, p, subtag='', mod='') -> str:
        def bind_fmt():
            return f'{pref}bindsym {keybind.strip()} ' + \
                f' ${mod} {cmd.strip()} {tag}{subtag}{postfix}'.strip() + '\n'
            
        ret, pref, postfix = '', '', ''
        mode = mode.removeprefix('mode_')
        bind_data = p.split('_')[1:]
        if subtag:
            subtag = f' {subtag}'
        if mode != 'default' and bind_data[0] == mode:
            pref, postfix = '\t', f', {conf_gen.mode_exit}'
            cmd = bind_data[1]
            if isinstance(settings[p], str):
                keybind = settings[p]
                ret += bind_fmt()
            elif isinstance(settings[p], list):
                for keybind in settings[p]:
                    ret += bind_fmt()
        else:
            if len(bind_data) == 1 and mode == 'default':
                cmd = bind_data[0]
                if isinstance(settings[p], str):
                    keybind = settings[p]
                    ret += bind_fmt()
                elif isinstance(settings[p], list):
                    for keybind in settings[p]:
                        ret += bind_fmt()
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

    def workspaces(self) -> str:
        ret = ''
        workspaces = self.cfg.get('workspaces', [])
        if workspaces:
            for index, ws in enumerate(workspaces):
                ret = f'{ret}set ${ws.split(":")[1]} "{index + 1} :: {ws}"\n'
        return ret

    def rules(self) -> str:
        ret=''
        for m in conf_gen.self_configured_modules:
            ret+=Rules.rules_mod(m)
        ret+=conf_gen.text_section(self.cfg.get('rules',''))
        return ret

    def mode(self, name, bind='', end=False) -> str:
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
        bindlist = self.cfg.get(mod, Bindmap())
        name = getattr(bindlist, 'name', '')
        if not name:
            name = mod
        ret = self.mode(
            name,
            bind=getattr(bindlist, "bind"),
            end=False)
        prefix = f'\tbindsym' if mod != 'mode_default' else 'bindsym'
        for kmap in bindlist:
            ret += '\n'
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
