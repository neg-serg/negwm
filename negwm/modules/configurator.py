""" i3 config generator """
import os
from datetime import datetime
from typing import List

from negwm.lib.misc import Misc
from negwm.lib.cfg import cfg
from negwm.lib.extension import extension
from negwm.lib.checker import checker
from negwm.lib.rules import Rules


class configurator(extension, cfg):
    mode_exit='mode "default"'
    header='# :>> NegWM'
    ending='# vim:filetype=i3config\n'
    create_header=Misc.create_header_tiny

    def __init__(self, i3) -> None:
        super().__init__()
        cfg.__init__(self, i3)
        self.i3ipc=i3
        self.conf_data=[]

    @staticmethod
    def configured_internally(module) -> bool:
        if not isinstance(module, cfg):
            return False
        if not hasattr(module, 'configured_internally'):
            return False
        if not isinstance(getattr(module, 'configured_internally'), bool):
            return False
        return bool(getattr(module, 'configured_internally'))


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
        self.fill(text=configurator.create_header('Module bindings'))
        self.fill(module_bindings=True)
        mods = extension.get_mods()
        for m in mods:
            module = mods[m]
            if configurator.configured_internally(module):
                self.fill(text=Rules.rules_mod(m))
        for cfg_section in self.cfg.keys():
            self.fill(text=configurator.create_header(f'Config section {cfg_section}'))
            self.fill(cfg_section)
        self.fill(text=configurator.ending)
        return '\n'.join(filter(None, self.conf_data))

    @staticmethod
    def module_binds(target_mode) -> str:
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
                    field = settings[param]
                    if param == 'binds':
                        ret += configurator.parse_binds(target_mode, tag, field, module=mod_name)
                    if isinstance(field, dict):
                        for inner_param in field:
                            if inner_param == 'binds':
                                ret += configurator.parse_binds(target_mode, tag, field[inner_param], module=mod_name, subtag=f' {param} ')
        return ret

    @staticmethod
    def parse_binds(target_mode, tag, binds, module='', subtag='') -> str:
        def bind_command():
            return f'{tab}bindsym {keybind.strip()} ' + \
                f' ${module} {cmd.strip()} {tag}{subtag}{exit}'.strip() + '\n'

        ret, tab, exit = '', '', ''
        if not isinstance(binds, dict):
            return ret
        for k,v in binds.items():
            if isinstance(v, list):
                mode='default'
                if mode == target_mode:
                    cmd=k
                    for keybind in v:
                        ret += bind_command()
            elif isinstance(v, dict):
                mode=k
                if mode == target_mode:
                    if mode != 'default':
                        tab, exit = '\t', f', {configurator.mode_exit}'
                    for sk, sv in v.items():
                        cmd=sk
                        for keybind in sv:
                            ret += bind_command()
        return ret

    def raw_ws(self) -> List:
        return self.cfg.get('workspaces', [])

    def workspaces(self) -> str:
        ret = ''
        workspaces = self.cfg.get('workspaces', [])
        if workspaces:
            for ws in workspaces:
                ret = f'{ret}set ${ws.split(":")[1]} "{ws}"\n'
        return ret

    def mode(self, mode, bind='', end=False) -> str:
        ret = ''
        mode = mode.removeprefix('mode_')
        if mode == 'default':
            return ret
        if not end:
            if bind:
                ret = f'{ret}bindsym {bind} mode "{mode}"\n'
            return f'{ret}mode {mode} {{'
        else:
            escape_bindings = ['Return', 'Escape', 'space', 'Control+C', 'Control+G']
            for keybind in escape_bindings:
                ret = f'{ret}\tbindsym {keybind}, {configurator.mode_exit}\n'
            return ret + '}\n'

    def bind(self, section) -> str:
        if not section:
            return ''
        bindlist = self.cfg.get(section, {})
        if 'binds' not in bindlist:
            return ''
        try:
            bind = bindlist['state'].get('bind', {})
        except:
            return ''
        if 'state' not in bindlist:
            name = ''
        else:
            name = bindlist['state'].get('name', '')
        if not name:
            name = section
        ret = self.mode(name, bind=bind, end=False)
        prefix = f'\tbindsym' if section != 'default' else 'bindsym'
        for kmap in bindlist['binds']:
            ret += '\n'
            Exit = kmap.get('exit', False)
            if not isinstance(Exit, bool):
                Exit = False
            Command = kmap.get('command', '')
            end = f', {configurator.mode_exit}' if Exit else ''
            for key, val in kmap.items():
                if key in {'exit', 'command'}: continue
                if isinstance(val, str) and isinstance(key, str):
                    # key: binding, val: action
                    if '{cmd}' not in Command:
                        if Command:
                            command = f'{Command} '
                        else:
                            command = Command
                        ret += f'{prefix} {key} {command}{val}{end}\n'
                    else:
                        format = Command
                        format = format.replace('{cmd}', val)
                        ret += f'{prefix} {key} {format}{end}\n'
                if isinstance(val, list) and not isinstance(key, tuple):
                    for b in val:
                        if '{cmd}' not in Command:
                            ret += f'{prefix} {b} {Command} {key}{end}\n'
                        else:
                            format = Command
                            format = format.replace('{cmd}', key)
                            ret += f'{prefix} {b} {format}{end}\n'
        ret += f'{configurator.module_binds(section)}{self.mode(section, end=True)}'
        return ret
