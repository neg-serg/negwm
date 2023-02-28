import os
from datetime import datetime
from typing import List

from negwm.lib.misc import Misc
from negwm.lib.cfg import cfg
from negwm.lib.extension import extension
from negwm.lib.checker import checker
from negwm.lib.rules import Rules
from negwm.lib.keymap import bindmap as Bindmap


class configurator(extension, cfg):
    mode_exit='mode "default"'
    header=Misc.create_header('NegWM')
    ending='# vim:filetype=i3config\n'

    def __init__(self, i3) -> None:
        super().__init__()
        cfg.__init__(self, i3)
        self.i3ipc=i3
        self.conf_data=[]

    @staticmethod
    def configured_internally(module):
        if not isinstance(module, cfg):
            return False
        return 'configured_internally' in module.cfg and module.cfg['configured_internally']


    def print(self) -> None: print(self.generate_config())

    def write(self, preserve_history=False):
        cfg, test_cfg = 'config', '.config_test'
        i3_cfg_dir = Misc.i3path()
        generated_cfg = self.generate_config()
        with open(f'{i3_cfg_dir}/{test_cfg}', 'w', encoding='utf8') as testi3:
            testi3.write(generated_cfg)
        if checker.check_i3_config(cfg=test_cfg):
            i3cfg_lines = []
            delete_from_here = False
            with open(f'{i3_cfg_dir}/{cfg}', 'r', encoding='utf8') as i3cfg:
                for line in i3cfg:
                    if configurator.header.split('\n')[0] in line:
                        delete_from_here = True
                    if line == configurator.ending:
                        delete_from_here = False
                    elif not delete_from_here:
                        i3cfg_lines.append(line)
            with open(f'{i3_cfg_dir}/{cfg}', 'w', encoding='utf8') as i3cfg:
                i3cfg.write(''.join(i3cfg_lines))
            with open(f'{i3_cfg_dir}/{cfg}', 'a', encoding='utf8') as i3cfg:
                i3cfg.write(generated_cfg)
                self.i3ipc.command('reload')
        if os.path.isfile(f'{i3_cfg_dir}/{test_cfg}'):
            if preserve_history:
                os.replace(f'{i3_cfg_dir}/{test_cfg}', f'{i3_cfg_dir}/{test_cfg}_{datetime.today().strftime("%Y-%m-%d-%H-%M-%S")}')
            else:
                os.remove(f'{i3_cfg_dir}/{test_cfg}')

    def fill(self, section='', text='', module_bindings=False) -> None:
        if module_bindings:
            mods=extension.get_mods()
            if mods is None or not mods:
                pass
            for mod in sorted(mods):
                self.conf_data.append(f'set ${mod} nop {mod}')
            self.conf_data.append('')
            return
        self.conf_data.append(self.bind(section))
        if text and text is not None:
            self.conf_data.append(text)
            return
        if hasattr(self, section):
            section_handler=getattr(self, section)
            self.conf_data.append(section_handler())
            return

    def generate_config(self) -> str:
        self.conf_data=[]
        self.fill(text=configurator.header)
        self.fill(text=Misc.create_header('Module bindings'))
        self.fill(module_bindings=True)
        mods = extension.get_mods()
        for m in mods:
            module = mods[m]
            if configurator.configured_internally(module):
                self.fill(text=Rules.rules_mod(m))
        for cfg_section in self.cfg.keys():
            self.fill(text=Misc.create_header(f'Config section {cfg_section}'))
            self.fill(cfg_section)
        self.fill(text=configurator.ending)
        return '\n'.join(filter(None, self.conf_data))

    @staticmethod
    def generate_bindsym(mode, tag, settings, p, subtag='', module='') -> str:
        def bind_fmt():
            return f'{pref}bindsym {keybind.strip()} ' + \
                f' ${module} {cmd.strip()} {tag}{subtag}{postfix}'.strip() + '\n'
            
        ret, pref, postfix = '', '', ''
        bind_data = p.split('_')[1:]
        if subtag:
            subtag = f' {subtag}'
        if mode != 'default' and bind_data[0] == mode:
            pref, postfix = '\t', f', {configurator.mode_exit}'
            cmd = bind_data[1]
            if isinstance(settings[p], str):
                keybind = settings[p]
                ret += bind_fmt()
            elif isinstance(settings[p], list):
                for keybind in settings[p]:
                    ret += bind_fmt()
        else:
            if mode == 'default' and len(bind_data) == 1:
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
        for mod_name in mods.keys():
            mod = mods[mod_name]
            if not configurator.configured_internally(mod):
                continue
            for tag, settings in mod.cfg.items():
                if not isinstance(settings, dict):
                    continue
                for param in settings:
                    if isinstance(settings[param], dict):
                        for param_name in settings[param]:
                            if param_name.startswith('keybind_'):
                                ret += configurator.generate_bindsym(
                                    mode, tag, settings[param], param_name, subtag=param, module=mod_name
                                )
                    elif param.startswith('keybind_'):
                        ret += configurator.generate_bindsym(mode, tag, settings, param, module=mod_name)
        return ret

    def raw_ws(self) -> List:
        return self.cfg.get('workspaces', [])

    def workspaces(self) -> str:
        ret = ''
        workspaces = self.cfg.get('workspaces', [])
        if workspaces:
            for index, ws in enumerate(workspaces):
                ret = f'{ret}set ${ws.split(":")[1]} "{index + 1} :: {ws}"\n'
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
            escape_bindings = ['Return', 'Escape', 'space', 'Control+C', 'Control+G']
            for keybind in escape_bindings:
                ret = f'{ret}\tbindsym {keybind}, {configurator.mode_exit}\n'
            return ret + '}\n'

    def bind(self, mod) -> str:
        if not mod:
            return ''
        bindlist = self.cfg.get(mod, Bindmap())
        try:
            bind = getattr(bindlist, 'bind')
        except AttributeError:
            return ''
        name = getattr(bindlist, 'name', '')
        if not name:
            name = mod
        ret = self.mode(
            name,
            bind=bind,
            end=False)
        prefix = f'\tbindsym' if mod != 'default' else 'bindsym'
        for kmap in bindlist:
            ret += '\n'
            end = f', {configurator.mode_exit}' if kmap.exit else ''
            for key, val in kmap.items():
                if isinstance(val, str) and isinstance(key, str):
                    # key: binding, val: action
                    if '{cmd}' not in kmap.fmt:
                        if kmap.fmt:
                            fmt = f'{kmap.fmt} '
                        else:
                            fmt = kmap.fmt
                        ret += f'{prefix} {key} {fmt}{val}{end}\n'
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
        ret += f'{configurator.module_binds(mod)}{self.mode(mod, end=True)}'
        return ret
